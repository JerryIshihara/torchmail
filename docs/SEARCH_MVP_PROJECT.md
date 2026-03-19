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
| Deployment config | **New** | `railway.toml`, `vercel.json`, GitHub Actions |

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

## GitHub Project Board Setup

1. Go to https://github.com/JerryIshihara/torchmail → **Projects** → **New project**
2. Choose **Board** template → name it **Search MVP**
3. Create columns:

| Column | Issues |
|--------|--------|
| **Backlog** | — |
| **To Do** | #29 (DB schema) |
| **In Progress** | — |
| **In Review** | — |
| **Done** | — |

4. Add all 6 issues (#25–#30) to the project
5. Suggested execution order:
   - Start #29 (schema) and #25 (backend API) simultaneously
   - #26 (region ranking) and #28 (frontend with mock data) can start right after
   - #27 (scraper) needs #25 done first
   - #30 (deploy) is last

---

## Success criteria for the MVP

- [ ] User types a research area → gets top 50 professors globally
- [ ] Results show US/UK/HK/SG labs first
- [ ] Each result shows the **exact paragraph** where the lab mentions hiring, with source URL
- [ ] Cached searches return in < 1 second
- [ ] Deployed to a public URL, no login required
