"""Utilities for finding and scraping lab hiring pages."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

try:
    from src.search_engine import config
except ModuleNotFoundError:
    from search_engine import config


REQUEST_TIMEOUT_SECONDS = 10.0
RATE_LIMIT_SECONDS = 0.6
MAX_CANDIDATE_LINKS = 6
MAX_PROFILE_URL_CANDIDATES = 12
USER_AGENT = "TorchMailBot/0.1 (+https://github.com/JerryIshihara/torchmail)"

HIRING_KEYWORDS = [
    "seeking",
    "looking for",
    "open position",
    "phd student",
    "postdoc",
    "research assistant",
    "ra position",
    "join my lab",
    "join our lab",
    "funded position",
    "hiring",
    "apply",
    "accepting applications",
    "research associate",
    "openings",
]
TARGET_LINK_HINTS = ("join", "position", "hiring", "openings", "people", "opportunities", "jobs", "apply")


@dataclass
class HiringInfo:
    paragraph: str
    url: str
    scraped_at: datetime
    keywords_matched: list[str]


@dataclass
class AuthorUrlHints:
    homepage_url: str | None = None
    works_api_url: str | None = None


@dataclass
class InstitutionUrlHint:
    homepage_url: str | None = None


_KEYWORD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (keyword, re.compile(r"\b" + re.escape(keyword).replace(r"\ ", r"\s+") + r"\b", re.IGNORECASE))
    for keyword in HIRING_KEYWORDS
]


class _HTMLSignalsParser(HTMLParser):
    """Extract text blocks and links from HTML."""

    _BLOCK_TAGS = {"p", "li", "div", "section", "article"}

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.text_blocks: list[str] = []
        self._block_parts: list[str] = []
        self._is_in_block = False
        self._current_link: str | None = None
        self._link_text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            self._current_link = href
            self._link_text_parts = []
        if tag in self._BLOCK_TAGS:
            self._is_in_block = True
            self._block_parts = []
        if tag == "br" and self._is_in_block:
            self._block_parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            if self._current_link:
                link_text = _compact_whitespace(" ".join(self._link_text_parts))
                self.links.append((self._current_link, link_text))
            self._current_link = None
            self._link_text_parts = []
        if tag in self._BLOCK_TAGS and self._is_in_block:
            text = _compact_whitespace(" ".join(self._block_parts))
            if len(text) >= 40:
                self.text_blocks.append(text)
            self._is_in_block = False
            self._block_parts = []

    def handle_data(self, data: str) -> None:
        text = _compact_whitespace(data)
        if not text:
            return
        if self._current_link is not None:
            self._link_text_parts.append(text)
        if self._is_in_block:
            self._block_parts.append(text)


def _compact_whitespace(value: str) -> str:
    return " ".join(value.split())


def _normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    path = parsed.path or ""
    return parsed._replace(fragment="", params="", query="", path=path).geturl()


def _extract_hiring_snippet(text_blocks: list[str]) -> tuple[str, list[str]] | None:
    for index, text in enumerate(text_blocks):
        keywords = sorted({keyword for keyword, pattern in _KEYWORD_PATTERNS if pattern.search(text)})
        if not keywords:
            continue

        context_blocks: list[str] = []
        if index > 0:
            context_blocks.append(text_blocks[index - 1])
        context_blocks.append(text)
        if index + 1 < len(text_blocks):
            context_blocks.append(text_blocks[index + 1])

        snippet = _compact_whitespace(" ".join(context_blocks))
        return snippet, keywords
    return None


def _discover_target_links(base_url: str, links: list[tuple[str, str]]) -> list[str]:
    base_host = urlparse(base_url).netloc
    candidates: list[str] = []
    seen = {base_url}

    for href, label in links:
        resolved = _normalize_url(urljoin(base_url, href))
        if resolved is None or resolved in seen:
            continue
        if urlparse(resolved).netloc != base_host:
            continue

        hint_text = f"{urlparse(resolved).path} {label}".lower()
        if any(hint in hint_text for hint in TARGET_LINK_HINTS):
            candidates.append(resolved)
            seen.add(resolved)
        if len(candidates) >= MAX_CANDIDATE_LINKS:
            break
    return candidates


def fetch_openalex_author_urls(openalex_id: str | None) -> AuthorUrlHints:
    """Fetch homepage hints from OpenAlex author metadata."""
    if not openalex_id:
        return AuthorUrlHints()

    author_id = openalex_id.rstrip("/").split("/")[-1]
    endpoint = f"{config.OPENALEX_BASE_URL}/authors/{author_id}"
    params = {"mailto": config.OPENALEX_EMAIL} if config.OPENALEX_EMAIL else None
    headers = {"User-Agent": USER_AGENT}

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True, headers=headers) as client:
            response = client.get(endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return AuthorUrlHints()

    return AuthorUrlHints(
        homepage_url=_normalize_url(payload.get("homepage_url")),
        works_api_url=_normalize_url(payload.get("works_api_url")),
    )


def fetch_openalex_institution_homepage(university_name: str | None, country_code: str | None) -> InstitutionUrlHint:
    """Fetch institution homepage hints from OpenAlex metadata."""
    if not university_name:
        return InstitutionUrlHint()

    params: dict[str, str | int] = {
        "search": university_name,
        "per-page": 5,
    }
    if country_code:
        params["filter"] = f"country_code:{country_code.upper()}"
    if config.OPENALEX_EMAIL:
        params["mailto"] = config.OPENALEX_EMAIL

    headers = {"User-Agent": USER_AGENT}
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True, headers=headers) as client:
            response = client.get(f"{config.OPENALEX_BASE_URL}/institutions", params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return InstitutionUrlHint()

    results = payload.get("results", [])
    if not isinstance(results, list):
        return InstitutionUrlHint()

    target_name = university_name.strip().casefold()
    target_country = country_code.upper() if country_code else None

    for result in results:
        if not isinstance(result, dict):
            continue
        homepage = _normalize_url(result.get("homepage_url"))
        if not homepage:
            continue
        display_name = str(result.get("display_name", "")).strip().casefold()
        result_country = result.get("country_code")
        if display_name == target_name and (not target_country or result_country == target_country):
            return InstitutionUrlHint(homepage_url=homepage)

    for result in results:
        if not isinstance(result, dict):
            continue
        homepage = _normalize_url(result.get("homepage_url"))
        result_country = result.get("country_code")
        if homepage and (not target_country or result_country == target_country):
            return InstitutionUrlHint(homepage_url=homepage)

    return InstitutionUrlHint()


def _name_tokens(professor_name: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[A-Za-z]+", professor_name)]
    honorifics = {"dr", "prof", "professor", "mr", "mrs", "ms"}
    while tokens and tokens[0] in honorifics:
        tokens.pop(0)
    return tokens


def _professor_profile_candidates(base_url: str, professor_name: str) -> list[str]:
    tokens = _name_tokens(professor_name)
    if not tokens:
        return []

    first = tokens[0]
    last = tokens[-1]
    full_slug = "-".join(tokens)
    first_last_slug = f"{first}-{last}"
    initial_last_slug = f"{first[:1]}{last}"

    slugs: list[str] = []
    for slug in (last, first_last_slug, full_slug, initial_last_slug):
        if slug and slug not in slugs:
            slugs.append(slug)

    path_templates = (
        "/people/{slug}",
        "/person/{slug}",
        "/faculty/{slug}",
        "/staff/{slug}",
        "/lab/{slug}",
        "/~{slug}",
    )

    candidates: list[str] = []
    for slug in slugs:
        for template in path_templates:
            candidate = _normalize_url(urljoin(base_url.rstrip("/") + "/", template.format(slug=slug)))
            if candidate and candidate not in candidates:
                candidates.append(candidate)
            if len(candidates) >= MAX_PROFILE_URL_CANDIDATES:
                return candidates
    return candidates


def _first_reachable_url(candidates: list[str]) -> str | None:
    if not candidates:
        return None

    headers = {"User-Agent": USER_AGENT}
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True, headers=headers) as client:
            for candidate in candidates:
                try:
                    response = client.get(candidate)
                except httpx.HTTPError:
                    continue
                if response.status_code >= 400:
                    continue
                content_type = response.headers.get("content-type", "").lower()
                if content_type and "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    continue
                return candidate
    except httpx.HTTPError:
        return None
    return None


def find_lab_url(
    professor_name: str,
    university_name: str | None,
    country_code: str | None,
    *,
    homepage_url: str | None = None,
    lab_url: str | None = None,
    openalex_id: str | None = None,
) -> str | None:
    """Return best-known lab/homepage URL for a professor."""
    trusted_candidates: list[str] = []
    for candidate in (lab_url, homepage_url):
        normalized = _normalize_url(candidate)
        if normalized and normalized not in trusted_candidates:
            trusted_candidates.append(normalized)

    if openalex_id:
        hints = fetch_openalex_author_urls(openalex_id)
        for candidate in (hints.homepage_url, hints.works_api_url):
            normalized = _normalize_url(candidate)
            if normalized and normalized not in trusted_candidates:
                trusted_candidates.append(normalized)

    if trusted_candidates:
        return trusted_candidates[0]

    institution_homepage = fetch_openalex_institution_homepage(university_name, country_code).homepage_url
    if institution_homepage is None:
        return None

    profile_candidates = _professor_profile_candidates(institution_homepage, professor_name)
    reachable = _first_reachable_url(profile_candidates)
    if reachable:
        return reachable
    return institution_homepage


def _robots_parser_for_origin(client: httpx.Client, origin: str) -> RobotFileParser | None:
    robots_url = f"{origin}/robots.txt"
    try:
        response = client.get(robots_url)
    except httpx.HTTPError:
        return None
    if response.status_code >= 400:
        return None
    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser


def _fetch_html_with_policy(
    client: httpx.Client,
    robots_cache: dict[str, RobotFileParser | None],
    url: str,
    last_request_at: float,
) -> tuple[str | None, float]:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    parser = robots_cache.get(origin)
    if origin not in robots_cache:
        parser = _robots_parser_for_origin(client, origin)
        robots_cache[origin] = parser

    if parser is not None and not parser.can_fetch(USER_AGENT, url):
        return None, last_request_at

    elapsed = time.monotonic() - last_request_at
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)

    try:
        response = client.get(url)
    except httpx.HTTPError:
        return None, time.monotonic()

    content_type = response.headers.get("content-type", "").lower()
    if response.status_code >= 400:
        return None, time.monotonic()
    if content_type and "text/html" not in content_type:
        return None, time.monotonic()
    return response.text, time.monotonic()


def _scrape_page_for_hiring(url: str, html: str) -> tuple[HiringInfo | None, list[str]]:
    parser = _HTMLSignalsParser()
    parser.feed(html)
    snippet = _extract_hiring_snippet(parser.text_blocks)
    if snippet:
        paragraph, keywords = snippet
        return (
            HiringInfo(
                paragraph=paragraph,
                url=url,
                scraped_at=datetime.now(timezone.utc),
                keywords_matched=keywords,
            ),
            [],
        )

    links = _discover_target_links(url, parser.links)
    return None, links


def scrape_hiring_info(url: str) -> HiringInfo | None:
    """Scrape homepage and targeted child links for hiring text."""
    normalized = _normalize_url(url)
    if normalized is None:
        return None

    headers = {"User-Agent": USER_AGENT}
    robots_cache: dict[str, RobotFileParser | None] = {}
    last_request_at = 0.0

    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True, headers=headers) as client:
        homepage_html, last_request_at = _fetch_html_with_policy(
            client=client,
            robots_cache=robots_cache,
            url=normalized,
            last_request_at=last_request_at,
        )
        if not homepage_html:
            return None

        info, links = _scrape_page_for_hiring(normalized, homepage_html)
        if info is not None:
            return info

        for link in links:
            html, last_request_at = _fetch_html_with_policy(
                client=client,
                robots_cache=robots_cache,
                url=link,
                last_request_at=last_request_at,
            )
            if not html:
                continue
            info, _ = _scrape_page_for_hiring(link, html)
            if info is not None:
                return info

    return None
