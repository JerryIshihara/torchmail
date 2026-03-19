"""Search client that queries the OpenAlex API and aggregates research opportunities."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from . import config


@dataclass
class AuthorRecord:
    openalex_id: str
    name: str
    orcid: str | None = None
    institution_id: str | None = None
    institution_name: str | None = None
    institution_country: str | None = None
    institution_type: str | None = None
    papers: list[dict] = field(default_factory=list)

    @property
    def paper_count(self) -> int:
        return len(self.papers)

    @property
    def total_citations(self) -> int:
        return sum(p.get("cited_by_count", 0) for p in self.papers)

    @property
    def avg_relevance(self) -> float:
        scores = [p.get("relevance_score", 0) or 0 for p in self.papers]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def latest_paper(self) -> dict | None:
        if not self.papers:
            return None
        return max(self.papers, key=lambda p: p.get("publication_date", "") or "")

    @property
    def latest_paper_date(self) -> str | None:
        lp = self.latest_paper
        return lp.get("publication_date") if lp else None

    @property
    def latest_paper_title(self) -> str | None:
        lp = self.latest_paper
        return lp.get("title") if lp else None

    def composite_score(self) -> float:
        """Weighted score: relevance (40%), activity (30%), citations (20%), recency (10%)."""
        relevance = min(self.avg_relevance / 50.0, 1.0) * 100
        activity = min(self.paper_count / 10.0, 1.0) * 100
        citation_score = min(self.total_citations / 100.0, 1.0) * 100

        recency = 0.0
        if self.latest_paper_date:
            try:
                d = datetime.strptime(self.latest_paper_date, "%Y-%m-%d")
                days_ago = (datetime.utcnow() - d).days
                recency = max(0, 100 - days_ago * 0.3)
            except ValueError:
                pass

        return (0.40 * relevance) + (0.30 * activity) + (0.20 * citation_score) + (0.10 * recency)


def _build_params(query: str, page: int) -> dict:
    today = datetime.utcnow()
    from_year = today.year - config.PUBLICATION_LOOKBACK_YEARS
    from_date = f"{from_year}-01-01"

    params: dict = {
        "search": query,
        "filter": f"from_publication_date:{from_date}",
        "sort": "relevance_score:desc",
        "per_page": config.OPENALEX_PER_PAGE,
        "page": page,
    }
    if config.OPENALEX_EMAIL:
        params["mailto"] = config.OPENALEX_EMAIL
    return params


def fetch_opportunities(query: str, on_progress=None) -> list[AuthorRecord]:
    """Fetch papers from OpenAlex and aggregate into per-author opportunity records."""
    authors: dict[str, AuthorRecord] = {}

    with httpx.Client(timeout=30.0) as client:
        for page in range(1, config.OPENALEX_PAGES_TO_FETCH + 1):
            params = _build_params(query, page)
            resp = client.get(f"{config.OPENALEX_BASE_URL}/works", params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])

            if not results:
                break

            for work in results:
                paper_info = {
                    "title": work.get("title"),
                    "publication_date": work.get("publication_date"),
                    "cited_by_count": work.get("cited_by_count", 0),
                    "relevance_score": work.get("relevance_score", 0),
                    "doi": work.get("doi"),
                }

                for authorship in work.get("authorships", []):
                    author = authorship.get("author", {})
                    aid = author.get("id")
                    if not aid:
                        continue

                    institutions = authorship.get("institutions", [])
                    inst = institutions[0] if institutions else {}

                    if aid not in authors:
                        authors[aid] = AuthorRecord(
                            openalex_id=aid,
                            name=author.get("display_name", "Unknown"),
                            orcid=author.get("orcid"),
                            institution_id=inst.get("id"),
                            institution_name=inst.get("display_name"),
                            institution_country=inst.get("country_code"),
                            institution_type=inst.get("type"),
                        )

                    authors[aid].papers.append(paper_info)

            if on_progress:
                on_progress(page, config.OPENALEX_PAGES_TO_FETCH)

            if page < config.OPENALEX_PAGES_TO_FETCH:
                time.sleep(0.15)

    ranked = sorted(authors.values(), key=lambda a: a.composite_score(), reverse=True)
    return ranked[: config.SEARCH_RESULT_LIMIT]
