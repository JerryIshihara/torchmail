"""FastAPI wrapper around the search engine pipeline."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import joinedload

try:
    from src.backend.scraper import NO_ACTIVE_HIRING_PAGE_MESSAGE, find_lab_url, scrape_hiring_info
    from src.search_engine import cache
    from src.search_engine import config as search_config
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
    from backend.scraper import NO_ACTIVE_HIRING_PAGE_MESSAGE, find_lab_url, scrape_hiring_info
    from search_engine import cache
    from search_engine import config as search_config
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

_SCRAPER_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="hiring-scraper")
_IN_FLIGHT_PROFESSOR_IDS: set[int] = set()
_IN_FLIGHT_LOCK = Lock()


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


@app.on_event("shutdown")
def _shutdown() -> None:
    _SCRAPER_EXECUTOR.shutdown(wait=False, cancel_futures=True)


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


def _serialize_opportunity(opportunity: ResearchOpportunity, rank: int | None = None) -> dict[str, Any]:
    professor = opportunity.professor
    university = professor.university if professor else None
    hiring_paragraph, hiring_url = _latest_active_hiring_signal(professor)
    if not hiring_paragraph:
        hiring_paragraph = NO_ACTIVE_HIRING_PAGE_MESSAGE
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
        "hiring_paragraph": hiring_paragraph,
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


def _schedule_hiring_backfill(opportunities: list[ResearchOpportunity]) -> None:
    for opportunity in opportunities:
        professor = opportunity.professor
        if professor is None or professor.id is None:
            continue

        existing_paragraph, existing_url = _latest_active_hiring_signal(professor)
        if existing_paragraph and existing_url:
            continue

        professor_id = professor.id
        with _IN_FLIGHT_LOCK:
            if professor_id in _IN_FLIGHT_PROFESSOR_IDS:
                continue
            _IN_FLIGHT_PROFESSOR_IDS.add(professor_id)

        _SCRAPER_EXECUTOR.submit(_scrape_and_store_hiring_signal, professor_id)


def _scrape_and_store_hiring_signal(professor_id: int) -> None:
    session = get_session()
    try:
        professor = (
            session.query(Professor)
            .options(
                joinedload(Professor.university),
                joinedload(Professor.hiring_signals),
            )
            .filter(Professor.id == professor_id)
            .first()
        )
        if professor is None:
            return

        existing_paragraph, existing_url = _latest_active_hiring_signal(professor)
        if existing_paragraph and existing_url:
            return

        university = professor.university
        resolved_lab_url = find_lab_url(
            professor_name=professor.name,
            university_name=university.name if university else None,
            country_code=university.country_code if university else None,
            homepage_url=professor.lab_url or professor.homepage_url,
            openalex_id=professor.openalex_id,
        )
        if not resolved_lab_url:
            return

        if professor.lab_url != resolved_lab_url:
            professor.lab_url = resolved_lab_url
        if not professor.homepage_url:
            professor.homepage_url = resolved_lab_url

        hiring_info = scrape_hiring_info(resolved_lab_url)
        if hiring_info is None:
            session.commit()
            return

        expires_at = hiring_info.scraped_at + timedelta(days=search_config.HIRING_SIGNAL_TTL_DAYS)
        existing_signal = (
            session.query(LabHiringSignal)
            .filter(
                LabHiringSignal.professor_id == professor.id,
                LabHiringSignal.hiring_url == hiring_info.url,
            )
            .first()
        )
        if existing_signal is None:
            session.add(
                LabHiringSignal(
                    professor_id=professor.id,
                    lab_url=resolved_lab_url,
                    hiring_url=hiring_info.url,
                    hiring_paragraph=hiring_info.paragraph,
                    keywords_matched=hiring_info.keywords_matched,
                    scraped_at=hiring_info.scraped_at,
                    expires_at=expires_at,
                    is_active=True,
                )
            )
        else:
            existing_signal.lab_url = resolved_lab_url
            existing_signal.hiring_paragraph = hiring_info.paragraph
            existing_signal.keywords_matched = hiring_info.keywords_matched
            existing_signal.scraped_at = hiring_info.scraped_at
            existing_signal.expires_at = expires_at
            existing_signal.is_active = True

        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
        with _IN_FLIGHT_LOCK:
            _IN_FLIGHT_PROFESSOR_IDS.discard(professor_id)


def _parse_countries_param(countries_param: str | None) -> list[str]:
    if not countries_param:
        return []
    return normalize_country_codes(countries_param.split(","))


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "cors_origins": _cors_origins()}


@app.get("/api/search")
def search(
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
        _schedule_hiring_backfill(opportunities)
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

        _schedule_hiring_backfill([opportunity])
        rank = _get_rank_for_opportunity(session, opportunity_id)
        return {
            "query": opportunity.query_topic,
            "result": _serialize_opportunity(opportunity, rank=rank),
        }
    finally:
        session.close()
