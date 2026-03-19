"""Unit tests for the search engine core logic."""

from __future__ import annotations

from datetime import datetime, timedelta

from search_engine import search as search_module
from search_engine.search import AuthorRecord


class TestAuthorRecord:
    def _make_author(self, **kwargs) -> AuthorRecord:
        defaults = {
            "openalex_id": "https://openalex.org/A000001",
            "name": "Dr. Test",
        }
        defaults.update(kwargs)
        return AuthorRecord(**defaults)

    def test_empty_papers(self):
        author = self._make_author()
        assert author.paper_count == 0
        assert author.total_citations == 0
        assert author.avg_relevance == 0.0
        assert author.latest_paper is None
        assert author.composite_score() == 0.0

    def test_paper_count(self):
        papers = [{"title": f"Paper {i}", "cited_by_count": 10} for i in range(5)]
        author = self._make_author(papers=papers)
        assert author.paper_count == 5

    def test_total_citations(self):
        papers = [
            {"cited_by_count": 10},
            {"cited_by_count": 25},
            {"cited_by_count": 0},
        ]
        author = self._make_author(papers=papers)
        assert author.total_citations == 35

    def test_avg_relevance(self):
        papers = [
            {"relevance_score": 40},
            {"relevance_score": 60},
        ]
        author = self._make_author(papers=papers)
        assert author.avg_relevance == 50.0

    def test_latest_paper(self):
        papers = [
            {"title": "Old", "publication_date": "2024-01-01"},
            {"title": "New", "publication_date": "2025-06-15"},
            {"title": "Mid", "publication_date": "2024-07-01"},
        ]
        author = self._make_author(papers=papers)
        assert author.latest_paper_title == "New"
        assert author.latest_paper_date == "2025-06-15"

    def test_composite_score_ranges(self):
        recent = (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d")
        papers = [
            {
                "title": "Recent work",
                "publication_date": recent,
                "cited_by_count": 50,
                "relevance_score": 40,
            }
        ]
        author = self._make_author(papers=papers)
        score = author.composite_score()
        assert 0 <= score <= 100

    def test_composite_score_higher_with_more_papers(self):
        recent = (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d")
        base_paper = {
            "publication_date": recent,
            "cited_by_count": 20,
            "relevance_score": 30,
        }
        author_few = self._make_author(papers=[base_paper])
        author_many = self._make_author(papers=[base_paper] * 8)
        assert author_many.composite_score() > author_few.composite_score()


def test_normalize_country_codes_dedupes_and_upcases():
    assert search_module.normalize_country_codes(["us", " GB ", "US", "", "hk"]) == ["US", "GB", "HK"]


def test_boosted_composite_score_adds_priority_bonus(monkeypatch):
    monkeypatch.setattr(search_module.config, "PRIORITY_COUNTRIES", ["US"])
    monkeypatch.setattr(search_module.config, "PRIORITY_COUNTRY_BOOST", 15.0)
    recent = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    author = AuthorRecord(
        openalex_id="https://openalex.org/A111",
        name="Dr. Priority",
        institution_country="US",
        papers=[{"publication_date": recent, "cited_by_count": 10, "relevance_score": 40}],
    )
    assert search_module.boosted_composite_score(author) == author.composite_score() + 15.0


def test_build_params_includes_country_filter_when_requested():
    params = search_module._build_params("robotics", 2, countries=["US", "GB"])
    assert params["search"] == "robotics"
    assert params["page"] == 2
    assert "institutions.country_code:US|GB" in params["filter"]


def test_fetch_opportunities_prioritizes_priority_country(monkeypatch):
    payload = {
        "results": [
            {
                "title": "Priority paper",
                "publication_date": "2025-04-01",
                "cited_by_count": 20,
                "relevance_score": 30,
                "doi": "10.1/priority",
                "authorships": [
                    {
                        "author": {"id": "https://openalex.org/A1", "display_name": "Priority Prof", "orcid": None},
                        "institutions": [
                            {
                                "id": "https://openalex.org/I1",
                                "display_name": "Priority University",
                                "country_code": "US",
                                "type": "education",
                            }
                        ],
                    }
                ],
            },
            {
                "title": "Non-priority paper",
                "publication_date": "2025-04-01",
                "cited_by_count": 20,
                "relevance_score": 30,
                "doi": "10.1/nonpriority",
                "authorships": [
                    {
                        "author": {"id": "https://openalex.org/A2", "display_name": "Non Priority Prof", "orcid": None},
                        "institutions": [
                            {
                                "id": "https://openalex.org/I2",
                                "display_name": "Non Priority University",
                                "country_code": "FR",
                                "type": "education",
                            }
                        ],
                    }
                ],
            },
        ]
    }

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return payload

    calls: list[dict] = []

    class DummyClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str, params: dict):
            calls.append(params)
            return DummyResponse()

    monkeypatch.setattr(search_module.httpx, "Client", DummyClient)
    monkeypatch.setattr(search_module.config, "OPENALEX_PAGES_TO_FETCH", 1)
    monkeypatch.setattr(search_module.config, "SEARCH_RESULT_LIMIT", 50)
    monkeypatch.setattr(search_module.config, "PRIORITY_COUNTRIES", ["US"])
    monkeypatch.setattr(search_module.config, "PRIORITY_COUNTRY_BOOST", 15.0)

    results = search_module.fetch_opportunities("machine learning", countries=["fr"])

    assert results[0].name == "Priority Prof"
    assert calls
    assert "institutions.country_code:FR" in calls[0]["filter"]
