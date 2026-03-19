"""PostgreSQL-based search cache.

Cache key = SHA-256 of the lowercased, whitespace-normalised query string.
Each cache entry has a TTL (default 24 h).  On hit within TTL the stored
opportunities are returned directly; on miss or expiry a fresh API search runs.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from . import config
from .db import (
    Professor,
    ResearchOpportunity,
    SearchCache,
    SearchCacheResult,
    University,
)
from .search import AuthorRecord


def _normalise_query(query: str) -> str:
    return " ".join(query.lower().split())


def _hash_query(query: str) -> str:
    return hashlib.sha256(_normalise_query(query).encode()).hexdigest()


def lookup(session: Session, query: str) -> list[ResearchOpportunity] | None:
    """Return cached opportunities for *query*, or None on cache miss / expiry."""
    qhash = _hash_query(query)
    now = datetime.now(timezone.utc)

    entry = (
        session.query(SearchCache)
        .filter(SearchCache.query_hash == qhash, SearchCache.expires_at > now)
        .first()
    )
    if entry is None:
        return None

    rows = (
        session.query(SearchCacheResult)
        .filter(SearchCacheResult.cache_id == entry.id)
        .options(
            joinedload(SearchCacheResult.opportunity).joinedload(
                ResearchOpportunity.professor
            ).joinedload(Professor.university)
        )
        .order_by(SearchCacheResult.rank)
        .all()
    )
    return [r.opportunity for r in rows]


def store(
    session: Session,
    query: str,
    authors: list[AuthorRecord],
) -> list[ResearchOpportunity]:
    """Persist search results and create a cache entry. Returns the stored opportunities."""
    qhash = _hash_query(query)

    old = session.query(SearchCache).filter(SearchCache.query_hash == qhash).first()
    if old:
        session.delete(old)
        session.flush()

    opportunities: list[ResearchOpportunity] = []

    for author in authors:
        university = _get_or_create_university(session, author)
        professor = _get_or_create_professor(session, author, university)

        opp = ResearchOpportunity(
            professor_id=professor.id,
            query_topic=_normalise_query(query),
            relevance_score=round(author.avg_relevance, 4),
            paper_count=author.paper_count,
            total_citations=author.total_citations,
            latest_paper_date=author.latest_paper_date,
            latest_paper_title=author.latest_paper_title,
            composite_score=round(author.composite_score(), 4),
        )
        session.add(opp)
        session.flush()
        opportunities.append(opp)

    now = datetime.now(timezone.utc)
    cache_entry = SearchCache(
        query_hash=qhash,
        raw_query=_normalise_query(query),
        created_at=now,
        expires_at=now + timedelta(hours=config.CACHE_TTL_HOURS),
    )
    session.add(cache_entry)
    session.flush()

    for rank, opp in enumerate(opportunities, start=1):
        link = SearchCacheResult(
            cache_id=cache_entry.id,
            opportunity_id=opp.id,
            rank=rank,
        )
        session.add(link)

    session.commit()

    for opp in opportunities:
        session.refresh(opp, ["professor"])
        if opp.professor:
            session.refresh(opp.professor, ["university"])

    return opportunities


def _get_or_create_university(session: Session, author: AuthorRecord) -> University | None:
    if not author.institution_id:
        return None
    uni = (
        session.query(University)
        .filter(University.openalex_id == author.institution_id)
        .first()
    )
    if uni:
        return uni
    uni = University(
        openalex_id=author.institution_id,
        name=author.institution_name or "Unknown",
        country_code=author.institution_country,
        type=author.institution_type,
    )
    session.add(uni)
    session.flush()
    return uni


def _get_or_create_professor(
    session: Session, author: AuthorRecord, university: University | None
) -> Professor:
    prof = (
        session.query(Professor)
        .filter(Professor.openalex_id == author.openalex_id)
        .first()
    )
    if prof:
        return prof
    prof = Professor(
        openalex_id=author.openalex_id,
        name=author.name,
        orcid=author.orcid,
        university_id=university.id if university else None,
    )
    session.add(prof)
    session.flush()
    return prof
