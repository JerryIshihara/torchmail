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
- `GET /api/search?q=machine+learning&countries=US,GB`
- `GET /api/search/{id}`

## Railway deployment

- Container config is in `src/backend/Dockerfile`
- Railway project config is in `/railway.json`
- Required environment variables: `DATABASE_URL`, `OPENALEX_EMAIL`, `BACKEND_CORS_ORIGINS`

## Hiring signal backfill

`GET /api/search` returns immediately, then schedules a background scraper that:

- resolves lab/homepage URLs from existing professor metadata and OpenAlex author metadata
- follows targeted pages (`join`, `positions`, `hiring`, `openings`, etc.)
- extracts raw hiring paragraphs and stores them in `lab_hiring_signals`

Until a signal is found, API responses use `"No active hiring page found"` for `hiring_paragraph`.
