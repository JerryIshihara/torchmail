# Production Deployment (Search MVP)

This guide covers Search MVP issue `#30`: deploy FastAPI backend to Railway, frontend to Vercel, and wire automatic production/preview deploys from GitHub Actions.

## Architecture

- Backend: Railway service running `src/backend` (`uvicorn src.backend.main:app`)
- Frontend: Vercel static deployment for `src/frontend` (Vite + React)
- Database: Supabase PostgreSQL via `DATABASE_URL`

## 1. Provision Supabase

### Connection mode — use Session Pooler for Railway

Supabase offers three connection modes. **Use Session Pooler** for Railway:

| Mode | Host | Port | IPv4? | SQLAlchemy safe? | When to use |
|------|------|------|-------|-----------------|-------------|
| **Session Pooler** ✅ | `aws-0-<region>.pooler.supabase.com` | 5432 | Yes | Yes | Railway (recommended) |
| Direct connection | `db.<ref>.supabase.co` | 5432 | No* | Yes | IPv6 infra or paid IPv4 add-on |
| Transaction Pooler | `aws-0-<region>.pooler.supabase.com` | 6543 | Yes | Partial† | Serverless / edge functions |

\* Direct connection uses IPv6 by default on new projects; Railway may fail to connect without the Supabase IPv4 Add-On ($4/mo).
† Transaction Pooler disables server-side prepared statements; the engine handles this automatically when port 6543 is detected.

### Steps

1. Create a Supabase project at https://app.supabase.com.
2. Go to **Project → Connect → Session pooler** and copy the connection string.
   It looks like:
   ```
   postgresql://postgres.<project-ref>:[PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```
3. Set `DATABASE_URL` to that string in Railway's environment variables.
4. Schema init runs automatically via Railway's `releaseCommand` on every deploy (see `railway.json`).
   To run it manually from any machine that can reach the database:

```bash
DATABASE_URL=<session-pooler-uri> PYTHONPATH=src python -m search_engine init-db
```

## 2. Deploy Backend to Railway

Repository includes `railway.json` and `src/backend/Dockerfile`.

Railway variables:

- `DATABASE_URL`: Supabase connection string
- `OPENALEX_EMAIL`: contact email for polite OpenAlex pool
- `BACKEND_CORS_ORIGINS`: comma-separated allowed frontend origins
- `CACHE_TTL_HOURS`: optional (default from app config)
- `HIRING_SIGNAL_TTL_DAYS`: optional (default from app config)

Health check:

- Path: `/api/health`

Release command (`railway.json` `releaseCommand` — runs before every deploy):

```bash
python -m search_engine init-db
```

Expected production start command (from container CMD):

```bash
uvicorn src.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## 3. Deploy Frontend to Vercel

Set Vercel project root directory to `src/frontend`.

Frontend runtime variables:

- `VITE_API_BASE_URL`: Railway backend public URL (for example, `https://torchmail-api.up.railway.app`)

If `VITE_API_BASE_URL` is not set, `src/frontend/vercel.json` rewrites `/api/*` to:

- `https://torchmail-api.up.railway.app/api/*`

## 4. GitHub Actions Auto-deploy

Workflow file: `.github/workflows/deploy.yml`

Trigger branches:

- `main` → production deploy hooks
- `claude/**`, `feature/**`, `fix/**`, `chore/**`, `cursor/**` → preview deploy hooks

Required repository secrets:

- `RAILWAY_DEPLOY_HOOK_PRODUCTION_URL`
- `RAILWAY_DEPLOY_HOOK_PREVIEW_URL`
- `VERCEL_DEPLOY_HOOK_PRODUCTION_URL`
- `VERCEL_DEPLOY_HOOK_PREVIEW_URL`

The workflow first verifies deploy artifacts:

- backend imports succeed
- frontend build succeeds

Then it triggers the provider deploy hooks via `curl`.
If a hook secret is missing, that deploy step is skipped with a clear log message.

## 5. Smoke Checks After Deploy

Backend:

```bash
curl -sS "https://<railway-backend>/api/health"
curl -sS "https://<railway-backend>/api/search?q=machine%20learning&countries=US,GB"
```

Frontend:

1. Open the Vercel URL.
2. Run a sample search.
3. Confirm results load and API calls return HTTP 200.

## 6. Known Constraints

- This repository can define deployment config and automation, but platform credentials and environment values must be provided in Railway/Vercel/GitHub settings.
- GitHub Project item status updates still require project write operations outside this repository.
