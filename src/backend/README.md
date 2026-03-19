# TorchMail Backend API

FastAPI wrapper for the existing search engine in `src/search_engine`.

## Run locally

```bash
python -m pip install -r src/backend/requirements.txt
uvicorn src.backend.main:app --reload
```

## Endpoints

- `GET /api/health`
- `GET /api/search?q=machine+learning`
- `GET /api/search/{id}`

## Hiring Signal Backfill

`/api/search` and `/api/search/{id}` now trigger a background scraper pass for
professors that do not currently have an active hiring signal cached in
`lab_hiring_signals`.

- Search responses are still returned immediately (non-blocking).
- While scraping is pending or no signal exists, the API returns:
  - `hiring_paragraph: "No active hiring page found"`
  - `hiring_url: null`
- Scraped entries are cached with a 7-day TTL via `expires_at`.
