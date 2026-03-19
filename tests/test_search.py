"""Unit tests for the search engine core logic."""

from __future__ import annotations

from datetime import datetime, timedelta

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
