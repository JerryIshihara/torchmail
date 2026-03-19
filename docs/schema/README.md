# Database Schema

This directory is the **single source of truth** for TorchMail's database design.

## Files

| File | Purpose |
|------|---------|
| [`schema.dbml`](schema.dbml) | Human-readable schema in [DBML](https://dbml.dbdiagram.io/docs) — **edit this first** |
| [`schema.sql`](schema.sql) | Equivalent SQL DDL for PostgreSQL — keep in sync with the DBML |

## Viewing the schema visually

1. Open **[dbdiagram.io](https://dbdiagram.io)**
2. Paste the contents of `schema.dbml` into the editor
3. The ER diagram renders automatically with colour-coded table groups:
   - **Blue** — MVP tables (in use now)
   - **Grey** — Phase 2 full-platform tables
   - **Orange** — Phase 3 student/matching tables

## Editing workflow

```text
1.  Edit schema.dbml          ← design change starts here
2.  Update schema.sql          ← keep the SQL in sync
3.  Update src/search_engine/db.py  ← update SQLAlchemy models to match
4.  Commit all three together
```

The SQLAlchemy models in `src/search_engine/db.py` implement the **MVP tables only**.
When promoting a Phase 2/3 table to active use, add the corresponding SQLAlchemy
model and uncomment the SQL in `schema.sql`.

## Convention

- MVP tables use `SERIAL` integer primary keys (simple, fast).
- Phase 2+ tables use `UUID` primary keys (better for distributed systems).
- All tables include `created_at TIMESTAMPTZ DEFAULT now()`.
- Tables with mutable rows also include `updated_at`.
- Naming: `snake_case`, plural table names, `_id` suffix for foreign keys.

## Provider notes

The SQL is standard PostgreSQL 14+ and works with:

| Provider | Free tier | Setup guide |
|----------|-----------|-------------|
| **[Supabase](https://supabase.com) (active)** | 500 MB, 2 projects | See `.env.example` — host: `db.kladhymmcqkaezikjhen.supabase.co` |
| [Neon](https://neon.tech) | 0.5 GB, branching | See `.env.example` |
| Local Docker | Unlimited | `docker compose up -d` |

To apply the MVP schema manually (providers auto-apply via SQLAlchemy on first run):

```bash
psql "$DATABASE_URL" -f docs/schema/schema.sql
```
