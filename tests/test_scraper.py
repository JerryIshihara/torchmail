"""Unit tests for backend hiring scraper utilities."""

from __future__ import annotations

from backend import scraper


class DummyResponse:
    def __init__(self, text: str = "", status_code: int = 200, content_type: str = "text/html") -> None:
        self.text = text
        self.status_code = status_code
        self.headers = {"content-type": content_type}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self) -> dict[str, str]:
        return {}


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
                    text=(
                        "<html><body>"
                        "<p>Welcome to the lab.</p>"
                        "<a href='/join'>Join us</a>"
                        "</body></html>"
                    )
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
