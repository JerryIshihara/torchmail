# TorchMail — Project Plan

> **Active scope: Search MVP only.** See [`SEARCH_MVP_PROJECT.md`](./SEARCH_MVP_PROJECT.md) for the full plan.

---

## Active Issues

| # | Title | What it does |
|---|-------|-------------|
| [#25](https://github.com/JerryIshihara/torchmail/issues/25) | **Backend API** | FastAPI wrapping existing search engine, JSON endpoints, CORS |
| [#26](https://github.com/JerryIshihara/torchmail/issues/26) | **Region ranking** | Two-tier sort: US/UK/HK/SG first, then rest of world |
| [#27](https://github.com/JerryIshihara/torchmail/issues/27) | **Lab hiring scraper** | Find lab page → extract exact hiring paragraph + URL |
| [#28](https://github.com/JerryIshihara/torchmail/issues/28) | **Frontend** | Single-page search UI with results list + hiring blockquotes |
| [#29](https://github.com/JerryIshihara/torchmail/issues/29) | **Database schema** | Add `lab_hiring_signals` table, update DBML/SQL |
| [#30](https://github.com/JerryIshihara/torchmail/issues/30) | **Deploy** | Vercel + Railway + Supabase, CI/CD |

## Dependency Graph

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

## Tech Stack (MVP)

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vite + React + Tailwind CSS |
| **Backend** | Python FastAPI |
| **Database** | Supabase (PostgreSQL) |
| **Research data** | OpenAlex API |
| **Deploy** | Vercel (frontend) + Railway (backend) |

## Database

- **Provider**: Supabase — `db.kladhymmcqkaezikjhen.supabase.co`
- **Schema source of truth**: [`docs/schema/`](./schema/)
- **Visual diagram**: Paste `schema.dbml` into [dbdiagram.io](https://dbdiagram.io)
