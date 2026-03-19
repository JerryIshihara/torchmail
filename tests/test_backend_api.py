"""Unit tests for the FastAPI search backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend import main as backend_main


class DummySession:
    def close(self) -> None:
        return None


def _make_opportunity() -> SimpleNamespace:
    university = SimpleNamespace(name="MIT", country_code="US", type="education")
    professor = SimpleNamespace(
        name="Dr. Jane Smith",
        orcid="0000-0001-2345-6789",
        openalex_id="https://openalex.org/A1234567",
        university=university,
        hiring_signals=[],
    )
    return SimpleNamespace(
        id=42,
        query_topic="genome analysis",
        paper_count=8,
        total_citations=142,
        latest_paper_date="2025-11-03",
        latest_paper_title="CRISPR-based genome editing in rare diseases",
        composite_score=87.3,
        professor=professor,
    )


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(backend_main, "init_db", lambda: None)
    return TestClient(backend_main.app)


def test_health_endpoint(monkeypatch):
    with _build_client(monkeypatch) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "http://localhost:3000" in payload["cors_origins"]


def test_search_endpoint_uses_pipeline_and_returns_structured_json(monkeypatch):
    opportunity = _make_opportunity()
    monkeypatch.setattr(backend_main, "get_session", lambda: DummySession())
    monkeypatch.setattr(backend_main, "_run_search_pipeline", lambda session, query, countries: ([opportunity], True))

    with _build_client(monkeypatch) as client:
        response = client.get("/api/search", params={"q": "  genome analysis  "})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "genome analysis"
    assert payload["countries"] == []
    assert payload["result_count"] == 1
    assert payload["from_cache"] is True
    assert payload["priority_count"] == 1
    assert payload["other_count"] == 0
    assert payload["results"][0]["rank"] == 1
    assert payload["results"][0]["professor"]["name"] == "Dr. Jane Smith"
    assert payload["results"][0]["is_priority_country"] is True
    assert payload["results"][0]["hiring_paragraph"] == "No active hiring page found"
    assert payload["results"][0]["hiring_url"] is None


def test_search_endpoint_uses_latest_active_hiring_signal(monkeypatch):
    opportunity = _make_opportunity()
    now = datetime.now(timezone.utc)
    opportunity.professor.hiring_signals = [
        SimpleNamespace(
            is_active=True,
            expires_at=now + timedelta(days=2),
            scraped_at=now - timedelta(hours=3),
            hiring_paragraph="Old hiring copy",
            hiring_url="https://lab.example.edu/openings-old",
        ),
        SimpleNamespace(
            is_active=True,
            expires_at=now + timedelta(days=2),
            scraped_at=now - timedelta(minutes=30),
            hiring_paragraph="We are looking for PhD students in ML systems.",
            hiring_url="https://lab.example.edu/openings",
        ),
    ]
    monkeypatch.setattr(backend_main, "get_session", lambda: DummySession())
    monkeypatch.setattr(backend_main, "_run_search_pipeline", lambda session, query, countries: ([opportunity], True))

    with _build_client(monkeypatch) as client:
        response = client.get("/api/search", params={"q": "genome analysis"})

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["hiring_paragraph"] == "We are looking for PhD students in ML systems."
    assert result["hiring_url"] == "https://lab.example.edu/openings"


def test_search_endpoint_parses_country_filters(monkeypatch):
    opportunity = _make_opportunity()
    monkeypatch.setattr(backend_main, "get_session", lambda: DummySession())
    captured: dict[str, object] = {}

    def fake_pipeline(session, query, countries):
        captured["query"] = query
        captured["countries"] = countries
        return [opportunity], False

    monkeypatch.setattr(backend_main, "_run_search_pipeline", fake_pipeline)

    with _build_client(monkeypatch) as client:
        response = client.get("/api/search", params={"q": "genome analysis", "countries": "us, gb ,US"})

    assert response.status_code == 200
    assert captured == {"query": "genome analysis", "countries": ["US", "GB"]}
    payload = response.json()
    assert payload["countries"] == ["US", "GB"]


def test_search_endpoint_rejects_blank_query(monkeypatch):
    monkeypatch.setattr(backend_main, "get_session", lambda: DummySession())
    monkeypatch.setattr(backend_main, "_run_search_pipeline", lambda session, query, countries: ([], False))

    with _build_client(monkeypatch) as client:
        response = client.get("/api/search", params={"q": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Query cannot be empty."


def test_search_detail_returns_single_result(monkeypatch):
    opportunity = _make_opportunity()
    monkeypatch.setattr(backend_main, "get_session", lambda: DummySession())
    monkeypatch.setattr(backend_main, "_fetch_opportunity_by_id", lambda session, opportunity_id: opportunity)
    monkeypatch.setattr(backend_main, "_get_rank_for_opportunity", lambda session, opportunity_id: 3)

    with _build_client(monkeypatch) as client:
        response = client.get("/api/search/42")

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "genome analysis"
    assert payload["result"]["id"] == 42
    assert payload["result"]["rank"] == 3


def test_search_detail_returns_404_when_missing(monkeypatch):
    monkeypatch.setattr(backend_main, "get_session", lambda: DummySession())
    monkeypatch.setattr(backend_main, "_fetch_opportunity_by_id", lambda session, opportunity_id: None)

    with _build_client(monkeypatch) as client:
        response = client.get("/api/search/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Opportunity not found."
