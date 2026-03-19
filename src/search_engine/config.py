import os


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://torchmail:torchmail_dev@localhost:5432/torchmail",
)

OPENALEX_BASE_URL = "https://api.openalex.org"

OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "")

CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))

SEARCH_RESULT_LIMIT = 50

OPENALEX_PAGES_TO_FETCH = 3
OPENALEX_PER_PAGE = 200
PUBLICATION_LOOKBACK_YEARS = 2
