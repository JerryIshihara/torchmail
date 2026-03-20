"""Unit tests for backend hiring scraper utilities."""

from __future__ import annotations

from backend import scraper


class DummyResponse:
    def __init__(
        self,
        text: str = "",
        status_code: int = 200,
        content_type: str = "text/html",
        json_payload: dict | None = None,
    ) -> None:
        self.text = text
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        self._json_payload = json_payload or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self) -> dict[str, str]:
        return self._json_payload


def test_find_lab_url_prefers_existing_urls():
    url = scraper.find_lab_url(
        professor_name="Dr. Jane Smith",
        university_name="MIT",
        country_code="US",
        lab_url="https://smith-lab.mit.edu",
        homepage_url="https://web.mit.edu/~jsmith",
    )
    assert url == "https://smith-lab.mit.edu"


def test_find_lab_url_falls_back_to_openalex_metadata(monkeypatch):
    monkeypatch.setattr(
        scraper,
        "fetch_openalex_author_urls",
        lambda openalex_id: scraper.AuthorUrlHints(homepage_url="https://lab.nus.edu.sg/openings", works_api_url=None),
    )
    url = scraper.find_lab_url(
        professor_name="Prof. Wei Chen",
        university_name="NUS",
        country_code="SG",
        openalex_id="https://openalex.org/A123",
    )
    assert url == "https://lab.nus.edu.sg/openings"


def test_find_lab_url_uses_institution_fallback_and_profile_heuristics(monkeypatch):
    monkeypatch.setattr(
        scraper,
        "fetch_openalex_author_urls",
        lambda openalex_id: scraper.AuthorUrlHints(homepage_url=None, works_api_url=None),
    )
    monkeypatch.setattr(
        scraper,
        "fetch_openalex_institution_homepage",
        lambda university_name, country_code: scraper.InstitutionUrlHint(homepage_url="https://www.mit.edu"),
    )

    seen_candidates: list[str] = []

    def fake_first_reachable(candidates: list[str]) -> str | None:
        seen_candidates.extend(candidates)
        return "https://www.mit.edu/faculty/jane-smith"

    monkeypatch.setattr(scraper, "_first_reachable_url", fake_first_reachable)
    url = scraper.find_lab_url(
        professor_name="Dr. Jane Smith",
        university_name="MIT",
        country_code="US",
        openalex_id="https://openalex.org/A999",
    )

    assert url == "https://www.mit.edu/faculty/jane-smith"
    assert "https://www.mit.edu/faculty/jane-smith" in seen_candidates


def test_find_lab_url_returns_institution_homepage_when_profiles_unreachable(monkeypatch):
    monkeypatch.setattr(
        scraper,
        "fetch_openalex_author_urls",
        lambda openalex_id: scraper.AuthorUrlHints(homepage_url=None, works_api_url=None),
    )
    monkeypatch.setattr(
        scraper,
        "fetch_openalex_institution_homepage",
        lambda university_name, country_code: scraper.InstitutionUrlHint(homepage_url="https://www.cam.ac.uk"),
    )
    monkeypatch.setattr(scraper, "_first_reachable_url", lambda candidates: None)

    url = scraper.find_lab_url(
        professor_name="Prof. Alice Brown",
        university_name="University of Cambridge",
        country_code="GB",
    )
    assert url == "https://www.cam.ac.uk"


def test_fetch_openalex_institution_homepage_prefers_exact_country_match(monkeypatch):
    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            self.requests: list[tuple[str, dict]] = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str, params=None, **kwargs) -> DummyResponse:
            self.requests.append((url, params or {}))
            return DummyResponse(
                json_payload={
                    "results": [
                        {
                            "display_name": "University of Example",
                            "country_code": "GB",
                            "homepage_url": "https://www.example.ac.uk",
                        },
                        {
                            "display_name": "University of Example",
                            "country_code": "US",
                            "homepage_url": "https://www.example.edu",
                        },
                    ]
                }
            )

    monkeypatch.setattr(scraper.httpx, "Client", DummyClient)
    hint = scraper.fetch_openalex_institution_homepage("University of Example", "GB")
    assert hint.homepage_url == "https://www.example.ac.uk"


def test_scrape_hiring_info_finds_paragraph_on_homepage(monkeypatch):
    monkeypatch.setattr(scraper, "RATE_LIMIT_SECONDS", 0.0)

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def get(self, url: str, **kwargs) -> DummyResponse:
            if url.endswith("/robots.txt"):
                return DummyResponse(status_code=404)
            if url == "https://lab.example.edu":
                return DummyResponse(
                    text=(
                        "<html><body>"
                        "<p>Our group studies distributed AI systems.</p>"
                        "<p>We are actively seeking PhD students and postdocs for funded positions.</p>"
                        "</body></html>"
                    )
                )
            raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(scraper.httpx, "Client", DummyClient)
    info = scraper.scrape_hiring_info("https://lab.example.edu")

    assert info is not None
    assert info.url == "https://lab.example.edu"
    assert "We are actively seeking PhD students and postdocs" in info.paragraph
    assert "seeking" in info.keywords_matched


def test_scrape_hiring_info_follows_targeted_link(monkeypatch):
    monkeypatch.setattr(scraper, "RATE_LIMIT_SECONDS", 0.0)

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def get(self, url: str, **kwargs) -> DummyResponse:
            if url.endswith("/robots.txt"):
                return DummyResponse(status_code=404)
            if url == "https://lab.example.edu":
                return DummyResponse(
                    text=("<html><body><p>Welcome to the lab.</p><a href='/join'>Join us</a></body></html>")
                )
            if url == "https://lab.example.edu/join":
                return DummyResponse(
                    text=(
                        "<html><body>"
                        "<p>Our lab works on biomedical NLP.</p>"
                        "<p>We are looking for research assistants and postdocs to join our lab.</p>"
                        "</body></html>"
                    )
                )
            raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(scraper.httpx, "Client", DummyClient)
    info = scraper.scrape_hiring_info("https://lab.example.edu")

    assert info is not None
    assert info.url == "https://lab.example.edu/join"
    assert "research assistants" in info.paragraph


def test_scrape_hiring_info_returns_none_without_hiring_signal(monkeypatch):
    monkeypatch.setattr(scraper, "RATE_LIMIT_SECONDS", 0.0)

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def get(self, url: str, **kwargs) -> DummyResponse:
            if url.endswith("/robots.txt"):
                return DummyResponse(status_code=404)
            return DummyResponse(
                text=(
                    "<html><body>"
                    "<p>Welcome to our research group website.</p>"
                    "<a href='/people'>People</a>"
                    "</body></html>"
                )
            )

    monkeypatch.setattr(scraper.httpx, "Client", DummyClient)
    info = scraper.scrape_hiring_info("https://lab.example.edu")
    assert info is None
