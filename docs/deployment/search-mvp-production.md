# Search MVP Production Deployment

This runbook deploys the current MVP stack:
- Frontend: Vite + React on Vercel
- Backend: FastAPI on Railway
- Database: Supabase PostgreSQL

## 1. Provision Supabase

1. Create a Supabase project.
2. Copy the Postgres connection string from `Settings -> Database`.
3. Apply the schema from `docs/schema/schema.sql` in the Supabase SQL editor.
4. Use the pooled connection string (PgBouncer) for production `DATABASE_URL`.

## 2. Deploy backend to Railway

The repository includes:
- `railway.toml` for build/start/healthcheck settings
- `Procfile` fallback process definition
- Root `requirements.txt` that installs backend + search engine dependencies

Set Railway environment variables:
- `DATABASE_URL`: Supabase pooled Postgres URL
- `OPENALEX_EMAIL`: contact email for OpenAlex polite pool
- `BACKEND_CORS_ORIGINS`: comma-separated frontend origins (for example `https://torchmail.vercel.app`)
- Optional: `CACHE_TTL_HOURS`, `HIRING_SIGNAL_TTL_DAYS`, `PRIORITY_COUNTRIES`, `PRIORITY_COUNTRY_BOOST`

Runtime behavior:
- Backend starts with `uvicorn src.backend.main:app --host 0.0.0.0 --port $PORT`
- `init_db()` runs at startup and creates required tables
- Health check endpoint: `/api/health`

## 3. Deploy frontend to Vercel

The repository includes `vercel.json` with build settings for `src/frontend`.

Set Vercel environment variables:
- `VITE_API_BASE_URL`: public Railway backend URL (for example `https://torchmail-api.up.railway.app`)

Build output:
- Vercel builds `src/frontend` and publishes `src/frontend/dist`

## 4. CI and deploy automation

CI (`.github/workflows/ci.yml`) now validates:
- Ruff lint + format check
- Python type checks (`mypy`) on search/ranking modules
- Pytest suite
- Python import/CLI smoke checks
- Frontend production build

Deploy workflow (`.github/workflows/deploy.yml`):
- Push to `main`: triggers production deploy hooks
- PR updates targeting `main`: triggers preview deploy hooks

Configure these repository secrets:
- `RAILWAY_PRODUCTION_DEPLOY_HOOK_URL`
- `VERCEL_PRODUCTION_DEPLOY_HOOK_URL`
- `RAILWAY_PREVIEW_DEPLOY_HOOK_URL` (optional)
- `VERCEL_PREVIEW_DEPLOY_HOOK_URL`

## 5. Smoke check

After production deploy:

```bash
curl "https://<backend-domain>/api/health"
curl "https://<backend-domain>/api/search?q=machine%20learning"
```

Open the Vercel URL and run a search from the UI to confirm end-to-end behavior.
