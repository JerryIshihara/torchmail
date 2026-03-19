"""Scraper utilities for extracting lab hiring paragraphs."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from threading import Lock
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

try:
    from src.search_engine import config
except ModuleNotFoundError:
    from search_engine import config

NO_ACTIVE_HIRING_PAGE_MESSAGE = "No active hiring page found"

SCRAPER_USER_AGENT = "TorchMailBot/0.1 (+https://github.com/JerryIshihara/torchmail)"
REQUEST_TIMEOUT_SECONDS = 10.0
REQUEST_INTERVAL_SECONDS = 0.6  # ~1.6 requests per second per domain.
MAX_LINKS_TO_FOLLOW = 8
MIN_PARAGRAPH_LENGTH = 40

HIRING_KEYWORDS = (
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
    "apply",
    "hiring",
    "accepting applications",
    "graduate student",
    "research associate",
    "openings",
)

LINK_HINTS = ("join", "position", "hiring", "openings", "opportunities", "people", "careers")

_HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", flags=re.IGNORECASE)
_SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style|noscript).*?>.*?</\1>")
_BLOCK_END_RE = re.compile(r"(?i)</(p|div|li|section|article|h1|h2|h3|h4|h5|h6|br)>")
_TAG_RE = re.compile(r"(?s)<[^>]+>")
_MULTISPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class HiringInfo:
    paragraph: str
    url: str
    scraped_at: datetime
    keywords_matched: list[str]


class _DomainRateLimiter:
    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval_seconds = min_interval_seconds
        self._last_request_ts: dict[str, float] = {}
        self._lock = Lock()

    def wait_turn(self, url: str) -> None:
        domain = urlparse(url).netloc.lower()
        if not domain:
            return

        with self._lock:
            now = time.monotonic()
            last = self._last_request_ts.get(domain, 0.0)
            wait_seconds = self._min_interval_seconds - (now - last)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
                now = time.monotonic()
            self._last_request_ts[domain] = now


_RATE_LIMITER = _DomainRateLimiter(min_interval_seconds=REQUEST_INTERVAL_SECONDS)


def _normalise_url(url: str | None) -> str | None:
    if not url:
        return None

    candidate = url.strip()
    if not candidate:
        return None
    if "://" not in candidate:
        candidate = f"https://{candidate.lstrip('/')}"

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return parsed._replace(fragment="").geturl()


def _request_openalex_json(path: str, params: dict[str, str] | None = None) -> dict | None:
    request_params = dict(params or {})
    if config.OPENALEX_EMAIL:
        request_params["mailto"] = config.OPENALEX_EMAIL

    endpoint = f"{config.OPENALEX_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.get(endpoint, params=request_params)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError):
        return None


def _author_short_id(openalex_id: str | None) -> str | None:
    if not openalex_id:
        return None
    candidate = openalex_id.rsplit("/", 1)[-1].strip()
    if not candidate:
        return None
    if candidate.startswith("A"):
        return candidate
    return None


def _author_homepage_from_openalex(openalex_id: str | None) -> str | None:
    author_id = _author_short_id(openalex_id)
    if not author_id:
        return None

    payload = _request_openalex_json(f"authors/{author_id}")
    if not isinstance(payload, dict):
        return None

    homepage = _normalise_url(payload.get("homepage_url"))
    if homepage:
        return homepage

    for institution in payload.get("last_known_institutions") or []:
        institution_homepage = _normalise_url(institution.get("homepage_url"))
        if institution_homepage:
            return institution_homepage

    return None


def _institution_homepage_from_openalex(university_name: str | None, country_code: str | None) -> str | None:
    if not university_name:
        return None

    params: dict[str, str] = {
        "search": university_name,
        "per-page": "5",
    }
    normalised_country = (country_code or "").strip().upper()
    if normalised_country:
        params["filter"] = f"country_code:{normalised_country}"

    payload = _request_openalex_json("institutions", params=params)
    if not isinstance(payload, dict):
        return None

    for institution in payload.get("results") or []:
        homepage = _normalise_url(institution.get("homepage_url"))
        if homepage:
            return homepage

    return None


def _dedupe_preserve_order(urls: list[str | None]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for url in urls:
        normalised = _normalise_url(url)
        if not normalised or normalised in seen:
            continue
        seen.add(normalised)
        unique.append(normalised)
    return unique


def _is_allowed_by_robots(client: httpx.Client, url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        _RATE_LIMITER.wait_turn(robots_url)
        response = client.get(robots_url)
        if response.status_code >= 400:
            return True
        parser.parse(response.text.splitlines())
        return parser.can_fetch(SCRAPER_USER_AGENT, url)
    except httpx.HTTPError:
        return True


def _fetch_html(client: httpx.Client, url: str) -> str | None:
    normalised_url = _normalise_url(url)
    if not normalised_url:
        return None

    if not _is_allowed_by_robots(client, normalised_url):
        return None

    try:
        _RATE_LIMITER.wait_turn(normalised_url)
        response = client.get(normalised_url)
    except httpx.HTTPError:
        return None

    if response.status_code in {403, 429}:
        return None
    if response.status_code >= 400:
        return None

    content_type = response.headers.get("content-type", "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return None

    return response.text


def _extract_candidate_links(html: str, base_url: str) -> list[str]:
    base = urlparse(base_url)
    links: list[str] = []
    seen: set[str] = set()

    for href in _HREF_RE.findall(html):
        absolute_url = _normalise_url(urljoin(base_url, href))
        if not absolute_url:
            continue

        parsed_link = urlparse(absolute_url)
        if parsed_link.netloc != base.netloc:
            continue

        lowered = absolute_url.lower()
        if not any(token in lowered for token in LINK_HINTS):
            continue
        if absolute_url in seen:
            continue

        seen.add(absolute_url)
        links.append(absolute_url)
        if len(links) >= MAX_LINKS_TO_FOLLOW:
            break

    return links


def _html_to_paragraphs(html: str) -> list[str]:
    no_scripts = _SCRIPT_STYLE_RE.sub(" ", html)
    with_breaks = _BLOCK_END_RE.sub("\n", no_scripts)
    without_tags = _TAG_RE.sub(" ", with_breaks)
    decoded = unescape(without_tags)

    lines: list[str] = []
    for line in decoded.splitlines():
        compact = _MULTISPACE_RE.sub(" ", line).strip()
        if len(compact) >= MIN_PARAGRAPH_LENGTH:
            lines.append(compact)
    return lines


def _matching_keywords(text: str) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in HIRING_KEYWORDS if keyword in lowered]


def _select_hiring_paragraph(paragraphs: list[str]) -> tuple[str, list[str]] | None:
    best_text: str | None = None
    best_keywords: list[str] = []
    best_score = -1.0

    for idx, paragraph in enumerate(paragraphs):
        keywords = _matching_keywords(paragraph)
        if not keywords:
            continue

        context_parts: list[str] = []
        if idx > 0:
            context_parts.append(paragraphs[idx - 1])
        context_parts.append(paragraph)
        if idx + 1 < len(paragraphs):
            context_parts.append(paragraphs[idx + 1])
        candidate_text = " ".join(context_parts).strip()

        score = (10.0 * len(set(keywords))) + (min(len(candidate_text), 600) / 100.0)
        if score > best_score:
            best_score = score
            best_text = candidate_text
            best_keywords = sorted(set(keywords))

    if best_text is None:
        return None
    return best_text, best_keywords


def find_lab_url(
    professor_name: str,
    university_name: str | None,
    country_code: str | None,
    homepage_url: str | None = None,
    openalex_id: str | None = None,
) -> str | None:
    """Best-effort lab homepage discovery using known URLs and OpenAlex metadata."""
    del professor_name  # Reserved for future heuristic expansion.

    candidates = _dedupe_preserve_order(
        [
            homepage_url,
            _author_homepage_from_openalex(openalex_id),
            _institution_homepage_from_openalex(university_name, country_code),
        ]
    )
    if not candidates:
        return None

    with httpx.Client(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": SCRAPER_USER_AGENT},
    ) as client:
        for candidate_url in candidates:
            html = _fetch_html(client, candidate_url)
            if html:
                return candidate_url

    return candidates[0]


def scrape_hiring_info(url: str) -> HiringInfo | None:
    """Scrape a lab site and return the most relevant hiring paragraph."""
    base_url = _normalise_url(url)
    if not base_url:
        return None

    with httpx.Client(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": SCRAPER_USER_AGENT},
    ) as client:
        base_html = _fetch_html(client, base_url)
        if not base_html:
            return None

        page_candidates = [base_url, *_extract_candidate_links(base_html, base_url)]
        best_info: HiringInfo | None = None
        best_keyword_count = 0

        for page_url in page_candidates:
            html = base_html if page_url == base_url else _fetch_html(client, page_url)
            if not html:
                continue

            paragraph_match = _select_hiring_paragraph(_html_to_paragraphs(html))
            if paragraph_match is None:
                continue

            paragraph_text, keywords = paragraph_match
            keyword_count = len(keywords)
            if keyword_count > best_keyword_count:
                best_keyword_count = keyword_count
                best_info = HiringInfo(
                    paragraph=paragraph_text,
                    url=page_url,
                    scraped_at=datetime.now(timezone.utc),
                    keywords_matched=keywords,
                )

        return best_info
