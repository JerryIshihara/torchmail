"""Unit tests for hiring scraper helpers."""

from __future__ import annotations

from backend import scraper


def test_select_hiring_paragraph_includes_neighbor_context():
    paragraphs = [
        "Our group builds robust robotics systems for real-world environments.",
        "We are actively seeking motivated PhD students and postdocs to join our lab this year.",
        "Please apply by emailing your CV and research statement to the PI.",
    ]

    match = scraper._select_hiring_paragraph(paragraphs)

    assert match is not None
    text, keywords = match
    assert "actively seeking motivated PhD students and postdocs" in text
    assert "our group builds robust robotics systems" in text.lower()
    assert "please apply by emailing your cv" in text.lower()
    assert "phd student" in keywords
    assert "postdoc" in keywords


def test_find_lab_url_uses_first_reachable_candidate(monkeypatch):
    monkeypatch.setattr(scraper, "_author_homepage_from_openalex", lambda openalex_id: "https://author.example")
    monkeypatch.setattr(
        scraper, "_institution_homepage_from_openalex", lambda university_name, country_code: "https://inst.example"
    )

    reachable_pages = {
        "https://author.example": "<html><body>Author lab page</body></html>",
    }
    monkeypatch.setattr(scraper, "_fetch_html", lambda client, url: reachable_pages.get(url))

    selected = scraper.find_lab_url(
        professor_name="Dr. Ada",
        university_name="Example University",
        country_code="US",
        homepage_url="https://missing.example",
        openalex_id="https://openalex.org/A123",
    )

    assert selected == "https://author.example"


def test_scrape_hiring_info_follows_targeted_links(monkeypatch):
    base_url = "https://lab.example.edu"
    join_url = "https://lab.example.edu/join"

    html_pages = {
        base_url: '<html><body><a href="/join">Join</a><p>Welcome to the lab homepage.</p></body></html>',
        join_url: (
            "<html><body><p>We are looking for PhD students with strong ML backgrounds "
            "and are currently hiring postdocs for funded projects.</p></body></html>"
        ),
    }
    monkeypatch.setattr(scraper, "_fetch_html", lambda client, url: html_pages.get(url))

    info = scraper.scrape_hiring_info(base_url)

    assert info is not None
    assert info.url == join_url
    assert "looking for PhD students" in info.paragraph
    assert "hiring" in info.keywords_matched
