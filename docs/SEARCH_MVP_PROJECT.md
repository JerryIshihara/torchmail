# Search MVP — Project Plan

> Focused scope: a working search backend + simple frontend that finds research
> opportunities and **quotes the exact paragraph + URL where the lab is hiring**.
> No auth. Priority regions: US, UK, HK, Singapore.

---

## What the user sees

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│       🔬 TorchMail Research Lab Search                       │
│                                                               │
│   ┌─────────────────────────────────────────────┐  ┌───────┐ │
│   │ bio-engineering in genome analysis          │  │Search │ │
│   └─────────────────────────────────────────────┘  └───────┘ │
│                                                               │
│   ─────────────────────────────────────────────────────────── │
│                                                               │
│   1. Dr. Jane Smith · MIT · US · Score 87.3                  │
│      8 papers · 142 citations · Latest: 2025-11-03           │
│      ┌──────────────────────────────────────────────────┐    │
│      │ "We are actively seeking PhD students and        │    │
│      │  postdocs with experience in CRISPR-based        │    │
│      │  genome editing for our NIH-funded project..."   │    │
│      │                                                  │    │
│      │  🔗 smith-lab.mit.edu/join                       │    │
│      └──────────────────────────────────────────────────┘    │
│                                                               │
│   2. Prof. Wei Chen · NUS · SG · Score 81.2                  │
│      ...                                                      │
│                                                               │
│   ─── Showing 42 results from US/UK/HK/SG, 8 from others ── │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Issues

| # | Title | What it does |
|---|-------|-------------|
| [#25](https://github.com/JerryIshihara/torchmail/issues/25) | **Backend API** | FastAPI wrapping existing search engine, JSON endpoints, CORS |
| [#26](https://github.com/JerryIshihara/torchmail/issues/26) | **Region ranking** | Two-tier sort: US/UK/HK/SG first, then rest of world |
| [#27](https://github.com/JerryIshihara/torchmail/issues/27) | **Lab hiring scraper** | Find lab page → extract exact hiring paragraph + URL |
| [#28](https://github.com/JerryIshihara/torchmail/issues/28) | **Frontend** | Single-page search UI with results list + hiring blockquotes |
| [#29](https://github.com/JerryIshihara/torchmail/issues/29) | **Database schema** | Add `lab_hiring_signals` table, update DBML/SQL |
| [#30](https://github.com/JerryIshihara/torchmail/issues/30) | **Deploy** | Vercel + Railway + Supabase, CI/CD |
| [#33](https://github.com/JerryIshihara/torchmail/issues/33) | **CI/CD** | Lint, test, build, security checks on every PR |

---

## Dependency graph

```
#29 DB schema ──────────────────────┐
                                    │
#25 Backend API ──┬─► #26 Region ──┼─► #27 Hiring scraper ──┐
                  │                 │                         │
                  └─► #28 Frontend ─┘                        │
                                                             ▼
                                                    #30 Deploy
```

**Critical path**: #29 + #25 → #26 + #27 → #28 → #30

Parallel tracks:
- **Track A** (#29, #25, #26): schema + API + ranking — backend team
- **Track B** (#28): frontend — can start with mock data, integrate later
- **Track C** (#27): scraper — can develop independently, plug into API

---

## How each piece works

### 1. Backend API (#25)

Wraps the existing `src/search_engine/` in FastAPI:

```
GET /api/search?q=genome+analysis          → top 50 results (JSON)
GET /api/search?q=genome+analysis&countries=US,GB  → filtered
GET /api/search/{opportunity_id}           → single result detail
GET /api/health                            → { "status": "ok" }
```

The response shape:

```json
{
  "query": "genome analysis",
  "result_count": 50,
  "from_cache": false,
  "priority_count": 42,
  "other_count": 8,
  "results": [
    {
      "rank": 1,
      "professor": {
        "name": "Dr. Jane Smith",
        "orcid": "0000-0001-2345-6789",
        "homepage_url": "https://smith-lab.mit.edu",
        "openalex_url": "https://openalex.org/A1234567"
      },
      "university": {
        "name": "Massachusetts Institute of Technology",
        "country_code": "US",
        "type": "education"
      },
      "paper_count": 8,
      "total_citations": 142,
      "latest_paper_date": "2025-11-03",
      "latest_paper_title": "CRISPR-based genome editing in...",
      "composite_score": 87.3,
      "is_priority_country": true,
      "hiring": {
        "paragraph": "We are actively seeking PhD students and postdocs with experience in CRISPR-based genome editing for our NIH-funded project on rare genetic disorders.",
        "url": "https://smith-lab.mit.edu/join",
        "scraped_at": "2026-03-18T14:30:00Z"
      }
    }
  ]
}
```

### 2. Region ranking (#26)

Two-tier sort applied after OpenAlex returns results:

| Tier | Countries | Boost |
|------|-----------|-------|
| 1 (priority) | US, GB, HK, SG | +15 to composite score |
| 2 (rest) | all others | no boost |

Results are ordered: all tier-1 by score descending, then all tier-2 by score descending. The `is_priority_country` flag in the response lets the frontend visually separate them.

### 3. Lab hiring scraper (#27)

The hardest piece. Pipeline per professor:

```
OpenAlex author metadata
    → extract homepage_url
    → if missing, try Google: "{name}" {university} lab
    → fetch homepage HTML
    → find links: /join, /positions, /openings, /opportunities, /hiring, /people
    → fetch those pages
    → regex/keyword scan for hiring paragraphs
    → extract paragraph with ±2 sentences context
    → store (paragraph, url, keywords_matched, scraped_at)
```

Hiring keywords (case-insensitive):
```
seeking, looking for, open position, PhD student, postdoc,
research assistant, join my lab, join our lab, funded position,
hiring, apply now, accepting applications, RA position,
graduate student, research associate, openings
```

**Async execution**: scraping runs in the background after search results are returned. The frontend polls or uses SSE to update hiring info as it becomes available.

### 4. Frontend (#28)

Minimal stack: **Vite + React + Tailwind CSS** (or Next.js — whichever is faster).

Components:
- `SearchBar` — centered input + button
- `ResultsList` — table/cards with professor info
- `ResultCard` — expandable card with hiring quote
- `HiringQuote` — blockquote with source URL
- `LoadingState` — skeleton cards
- `EmptyState` — "No results found"

No routing needed — single page.

### 5. Database schema (#29)

New table added to `docs/schema/schema.dbml` and SQLAlchemy models:

```dbml
Table lab_hiring_signals {
  id              int [pk, increment]
  professor_id    int [ref: > professors.id, not null]
  lab_url         text
  hiring_url      text [not null]
  hiring_paragraph text [not null]
  keywords_matched text[]
  scraped_at      timestamptz [not null, default: `now()`]
  expires_at      timestamptz [not null]
  is_active       boolean [default: true]

  indexes {
    professor_id
    (professor_id, hiring_url) [unique]
  }
}
```

Plus two new columns on `professors`: `homepage_url` and `lab_url`.

### 7. CI/CD (#33)

GitHub Actions pipeline (`.github/workflows/ci.yml`) runs on every push to `main`
and every PR targeting `main`:

| Job | Tool | What it checks |
|-----|------|----------------|
| **Lint** | `ruff check` + `ruff format` | Code style, import order, common bugs |
| **Test** | `pytest` | Unit tests in `tests/` |
| **Build** | Python import + CLI | All modules load, CLI entry point works |
| **Security** | `bandit` + `safety` | Code vulnerabilities, dependency CVEs |

A separate workflow (`.github/workflows/auto-add-bugs-to-board.yml`) watches for
issues labeled `bug` and auto-adds them to the project board.

### 6. Deploy (#30)

| Service | Provider | Cost |
|---------|----------|------|
| Frontend | Vercel (free tier) | $0 |
| Backend | Railway ($5 hobby) or Render (free) | $0–5/mo |
| Database | Supabase (free tier, 500 MB) | $0 |

Total: **$0–5/month**.

---

## What already exists vs what's new

| Component | Status | Location |
|-----------|--------|----------|
| OpenAlex search + ranking | **Exists** | `src/search_engine/search.py` |
| PostgreSQL models (University, Professor, Opportunity) | **Exists** | `src/search_engine/db.py` |
| Cache layer (SHA-256, TTL) | **Exists** | `src/search_engine/cache.py` |
| Config (env vars, .env) | **Exists** | `src/search_engine/config.py` |
| DBML + SQL schema | **Exists** | `docs/schema/` |
| FastAPI wrapper | **New** | `src/backend/` |
| Region-prioritized ranking | **New** | Modify `search.py` or post-process in API |
| Lab hiring scraper | **New** | `src/backend/scraper.py` |
| Frontend | **New** | `src/frontend/` |
| CI/CD pipeline | **New** | `.github/workflows/ci.yml`, `.github/workflows/auto-add-bugs-to-board.yml` |
| Ruff lint config | **New** | `ruff.toml` |
| Unit tests | **New** | `tests/test_search.py` |
| Deployment config | **New** | `railway.toml`, `vercel.json` |

---

## Out of scope

These are explicitly **not** part of this MVP:

- Authentication / user accounts
- Email generation
- Student profiles or matching
- Application tracking
- Payment / monetization
- Community features
- Admin panel
- Multiple search endpoints (just one: `/api/search`)

---

## GitHub Project Board

**Live board**: [Search MVP — GitHub Project](https://github.com/users/JerryIshihara/projects/7)

### Columns

| Column | Meaning |
|--------|---------|
| **Backlog** | Blocked by upstream dependencies |
| **Todo** | Ready to start |
| **In Progress** | Actively being worked on |
| **In Review** | PR open, awaiting review |
| **Done** | Complete and merged |

### Custom fields

| Field | Options |
|-------|---------|
| **Priority** | P0 — Critical Path · P1 — High · P2 — Normal |
| **Track** | A — Backend · B — Frontend · C — Scraper · D — Deploy |

### Board rules

| Rule | Trigger | Action |
|------|---------|--------|
| **Bug auto-add** | Issue opened or labeled with `bug` | Automatically added to the Search MVP board |
| **CI/CD gating** | Every PR targeting `main` | Must pass lint, test, build, and security checks before merge |

The bug auto-add rule is implemented via `.github/workflows/auto-add-bugs-to-board.yml`
and requires a `GH_PROJECT_TOKEN` repository secret with `project` scope.

### Current board state

| Issue | Status | Priority | Track |
|-------|--------|----------|-------|
| #33 CI/CD | In Progress | P0 | D — Deploy |
| #29 DB schema | Todo | P0 | A — Backend |
| #25 Backend API | Todo | P0 | A — Backend |
| #26 Region ranking | Backlog | P1 | A — Backend |
| #28 Frontend | Backlog | P1 | B — Frontend |
| #27 Lab hiring scraper | Backlog | P1 | C — Scraper |
| #30 Deploy | Backlog | P2 | D — Deploy |

### Execution order

1. **#33** (CI/CD) — in progress, protects all future PRs
2. Start **#29** (schema) and **#25** (backend API) simultaneously — both are P0
3. **#26** (region ranking) and **#28** (frontend with mock data) can start right after
4. **#27** (scraper) needs #25 done first
5. **#30** (deploy) is last

---

## Success criteria for the MVP

- [ ] User types a research area → gets top 50 professors globally
- [ ] Results show US/UK/HK/SG labs first
- [ ] Each result shows the **exact paragraph** where the lab mentions hiring, with source URL
- [ ] Cached searches return in < 1 second
- [ ] Deployed to a public URL, no login required
