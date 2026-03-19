"""Configuration — reads from environment variables or a .env file."""

import os
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
if _ENV_FILE.is_file():
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and value and key not in os.environ:
            os.environ[key] = value


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://torchmail:torchmail_dev@localhost:5432/torchmail",
)

OPENALEX_BASE_URL = "https://api.openalex.org"

OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "")

CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
HIRING_SIGNAL_TTL_DAYS = int(os.getenv("HIRING_SIGNAL_TTL_DAYS", "7"))

SEARCH_RESULT_LIMIT = 50

OPENALEX_PAGES_TO_FETCH = 3
OPENALEX_PER_PAGE = 200
PUBLICATION_LOOKBACK_YEARS = 2

PRIORITY_COUNTRIES = [
    code.strip().upper() for code in os.getenv("PRIORITY_COUNTRIES", "US,GB,HK,SG").split(",") if code.strip()
]
PRIORITY_COUNTRY_BOOST = float(os.getenv("PRIORITY_COUNTRY_BOOST", "15"))
