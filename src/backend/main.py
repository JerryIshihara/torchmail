"""FastAPI wrapper around the search engine pipeline."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

try:
    from src.backend.scraper import HiringInfo, find_lab_url, scrape_hiring_info
    from src.search_engine import cache, config
    from src.search_engine.db import (
        LabHiringSignal,
        Professor,
        ResearchOpportunity,
        SearchCacheResult,
        get_session,
        init_db,
    )
    from src.search_engine.search import fetch_opportunities, is_priority_country, normalize_country_codes
except ModuleNotFoundError:
    from backend.scraper import HiringInfo, find_lab_url, scrape_hiring_info
    from search_engine import cache, config
    from search_engine.db import (
        LabHiringSignal,
        Professor,
        ResearchOpportunity,
        SearchCacheResult,
        get_session,
        init_db,
    )
    from search_engine.search import fetch_opportunities, is_priority_country, normalize_country_codes

app = FastAPI(title="TorchMail Search API", version="0.1.0")
NO_ACTIVE_HIRING_TEXT = "No active hiring page found"


def _cors_origins() -> list[str]:
    origins = os.getenv("BACKEND_CORS_ORIGINS") or os.getenv("FRONTEND_ORIGIN") or "http://localhost:3000"
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def _latest_active_hiring_signal(professor: Professor | None) -> tuple[str | None, str | None]:
    if professor is None:
        return None, None

    signals = getattr(professor, "hiring_signals", None)
    if not signals:
        return None, None

    now = datetime.now(timezone.utc)
    active_signals = [
        signal
        for signal in signals
        if bool(getattr(signal, "is_active", True))
        and ((expires_at := getattr(signal, "expires_at", None)) is None or expires_at > now)
    ]
    if not active_signals:
        return None, None

    latest = max(
        active_signals, key=lambda signal: getattr(signal, "scraped_at", datetime.min.replace(tzinfo=timezone.utc))
    )
    return getattr(latest, "hiring_paragraph", None), getattr(latest, "hiring_url", None)


def _has_active_hiring_signal(professor: Professor | Any | None) -> bool:
    paragraph, _ = _latest_active_hiring_signal(professor)
    return bool(paragraph)


def _upsert_hiring_signal(
    session,
    professor: Professor,
    source_lab_url: str,
    hiring_info: HiringInfo,
) -> None:
    expires_at = hiring_info.scraped_at + timedelta(days=config.HIRING_SIGNAL_TTL_DAYS)
    existing = (
        session.query(LabHiringSignal)
        .filter(
            LabHiringSignal.professor_id == professor.id,
            LabHiringSignal.hiring_url == hiring_info.url,
        )
        .first()
    )
    if existing:
        existing.lab_url = source_lab_url
        existing.hiring_paragraph = hiring_info.paragraph
        existing.keywords_matched = hiring_info.keywords_matched
        existing.scraped_at = hiring_info.scraped_at
        existing.expires_at = expires_at
        existing.is_active = True
        return

    signal = LabHiringSignal(
        professor_id=professor.id,
        lab_url=source_lab_url,
        hiring_url=hiring_info.url,
        hiring_paragraph=hiring_info.paragraph,
        keywords_matched=hiring_info.keywords_matched,
        scraped_at=hiring_info.scraped_at,
        expires_at=expires_at,
        is_active=True,
    )
    session.add(signal)


def _backfill_hiring_signals(professor_ids: list[int]) -> None:
    session = get_session()
    try:
        for professor_id in professor_ids:
            try:
                professor = (
                    session.query(Professor)
                    .options(joinedload(Professor.university), joinedload(Professor.hiring_signals))
                    .filter(Professor.id == professor_id)
                    .first()
                )
                if professor is None or _has_active_hiring_signal(professor):
                    continue

                university = professor.university
                lab_url = find_lab_url(
                    professor_name=professor.name,
                    university_name=university.name if university else None,
                    country_code=university.country_code if university else None,
                    homepage_url=professor.homepage_url,
                    lab_url=professor.lab_url,
                    openalex_id=professor.openalex_id,
                )
                if not lab_url:
                    continue

                if not professor.homepage_url:
                    professor.homepage_url = lab_url
                professor.lab_url = lab_url

                hiring_info = scrape_hiring_info(lab_url)
                if hiring_info is None:
                    continue

                _upsert_hiring_signal(session, professor, lab_url, hiring_info)
                session.commit()
            except IntegrityError:
                session.rollback()
            except Exception:
                session.rollback()
    finally:
        session.close()


def _enqueue_hiring_backfill(background_tasks: BackgroundTasks, opportunities: list[ResearchOpportunity]) -> None:
    professor_ids: set[int] = set()

    for opportunity in opportunities:
        professor = getattr(opportunity, "professor", None)
        if not professor or _has_active_hiring_signal(professor):
            continue

        professor_id = getattr(professor, "id", None)
        if isinstance(professor_id, int):
            professor_ids.add(professor_id)

    if professor_ids:
        background_tasks.add_task(_backfill_hiring_signals, sorted(professor_ids))


def _serialize_opportunity(opportunity: ResearchOpportunity, rank: int | None = None) -> dict[str, Any]:
    professor = opportunity.professor
    university = professor.university if professor else None
    hiring_paragraph, hiring_url = _latest_active_hiring_signal(professor)
    country_code = university.country_code if university else None

    return {
        "id": opportunity.id,
        "rank": rank,
        "professor": {
            "name": professor.name if professor else None,
            "orcid": professor.orcid if professor else None,
            "openalex_id": professor.openalex_id if professor else None,
        },
        "university": {
            "name": university.name if university else None,
            "country_code": university.country_code if university else None,
            "type": university.type if university else None,
        },
        "paper_count": opportunity.paper_count,
        "total_citations": opportunity.total_citations,
        "latest_paper_date": opportunity.latest_paper_date,
        "latest_paper_title": opportunity.latest_paper_title,
        "composite_score": opportunity.composite_score,
        "hiring_paragraph": hiring_paragraph or NO_ACTIVE_HIRING_TEXT,
        "hiring_url": hiring_url,
        "is_priority_country": is_priority_country(country_code),
    }


def _run_search_pipeline(
    session,
    query: str,
    countries: list[str] | None = None,
) -> tuple[list[ResearchOpportunity], bool]:
    cached = cache.lookup(session, query, countries=countries)
    if cached is not None:
        return cached, True

    authors = fetch_opportunities(query, countries=countries)
    if not authors:
        return [], False

    return cache.store(session, query, authors, countries=countries), False


def _get_rank_for_opportunity(session, opportunity_id: int) -> int | None:
    row = (
        session.query(SearchCacheResult.rank)
        .filter(SearchCacheResult.opportunity_id == opportunity_id)
        .order_by(SearchCacheResult.rank.asc())
        .first()
    )
    return row[0] if row else None


def _fetch_opportunity_by_id(session, opportunity_id: int) -> ResearchOpportunity | None:
    return (
        session.query(ResearchOpportunity)
        .options(joinedload(ResearchOpportunity.professor).joinedload(Professor.university))
        .filter(ResearchOpportunity.id == opportunity_id)
        .first()
    )


def _build_search_response(
    query: str,
    opportunities: list[ResearchOpportunity],
    from_cache: bool,
    countries: list[str] | None = None,
) -> dict[str, Any]:
    serialized = [
        _serialize_opportunity(opportunity, rank=index) for index, opportunity in enumerate(opportunities, start=1)
    ]
    priority_count = sum(1 for item in serialized if item["is_priority_country"])
    other_count = len(serialized) - priority_count
    return {
        "query": query,
        "countries": countries or [],
        "result_count": len(serialized),
        "from_cache": from_cache,
        "priority_count": priority_count,
        "other_count": other_count,
        "results": serialized,
    }


def _parse_countries_param(countries_param: str | None) -> list[str]:
    if not countries_param:
        return []
    return normalize_country_codes(countries_param.split(","))


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "cors_origins": _cors_origins()}


@app.get("/api/search")
def search(
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1),
    countries: str | None = Query(None, description="Comma-separated ISO country codes (e.g. US,GB)"),
) -> dict[str, Any]:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    country_filter = _parse_countries_param(countries)

    session = get_session()
    try:
        opportunities, from_cache = _run_search_pipeline(session, query, countries=country_filter)
        _enqueue_hiring_backfill(background_tasks, opportunities)
        return _build_search_response(query, opportunities, from_cache, countries=country_filter)
    finally:
        session.close()


@app.get("/api/search/{opportunity_id}")
def search_detail(opportunity_id: int) -> dict[str, Any]:
    session = get_session()
    try:
        opportunity = _fetch_opportunity_by_id(session, opportunity_id)
        if opportunity is None:
            raise HTTPException(status_code=404, detail="Opportunity not found.")

        rank = _get_rank_for_opportunity(session, opportunity_id)
        return {
            "query": opportunity.query_topic,
            "result": _serialize_opportunity(opportunity, rank=rank),
        }
    finally:
        session.close()
