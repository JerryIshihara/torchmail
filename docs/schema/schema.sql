-- ─────────────────────────────────────────────────────────────────────
--  TorchMail — PostgreSQL Schema  (generated from schema.dbml)
--  Run against any PostgreSQL 14+ database (local, Supabase, Neon, …).
--
--  This file is the SQL companion of schema.dbml.  When the DBML
--  changes, regenerate this file or update it by hand and keep both
--  in sync.
-- ─────────────────────────────────────────────────────────────────────

-- ═══════════════════════════════════════════════════════════════════════
--  MVP TABLES  (used by src/search_engine/ right now)
-- ═══════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS universities (
    id            SERIAL PRIMARY KEY,
    openalex_id   VARCHAR(256) UNIQUE,
    name          VARCHAR(512) NOT NULL,
    country_code  VARCHAR(8),
    type          VARCHAR(64),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS professors (
    id            SERIAL PRIMARY KEY,
    openalex_id   VARCHAR(256) UNIQUE,
    name          VARCHAR(512) NOT NULL,
    orcid         VARCHAR(64),
    university_id INTEGER REFERENCES universities(id),
    homepage_url  TEXT,
    lab_url       TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lab_hiring_signals (
    id               SERIAL PRIMARY KEY,
    professor_id     INTEGER NOT NULL REFERENCES professors(id),
    lab_url          TEXT,
    hiring_url       TEXT NOT NULL,
    hiring_paragraph TEXT NOT NULL,
    keywords_matched TEXT[],
    scraped_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at       TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '7 days'),
    is_active        BOOLEAN NOT NULL DEFAULT true,
    UNIQUE (professor_id, hiring_url)
);
CREATE INDEX IF NOT EXISTS idx_hiring_signals_professor ON lab_hiring_signals(professor_id);
CREATE INDEX IF NOT EXISTS idx_hiring_signals_active ON lab_hiring_signals(is_active) WHERE is_active;

CREATE TABLE IF NOT EXISTS research_opportunities (
    id                 SERIAL PRIMARY KEY,
    professor_id       INTEGER NOT NULL REFERENCES professors(id),
    query_topic        TEXT NOT NULL,
    relevance_score    DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    paper_count        INTEGER NOT NULL DEFAULT 0,
    total_citations    INTEGER NOT NULL DEFAULT 0,
    latest_paper_date  VARCHAR(32),
    latest_paper_title TEXT,
    composite_score    DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS search_cache (
    id          SERIAL PRIMARY KEY,
    query_hash  VARCHAR(64) UNIQUE NOT NULL,
    raw_query   TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_search_cache_hash ON search_cache(query_hash);

CREATE TABLE IF NOT EXISTS search_cache_results (
    id              SERIAL PRIMARY KEY,
    cache_id        INTEGER NOT NULL REFERENCES search_cache(id) ON DELETE CASCADE,
    opportunity_id  INTEGER NOT NULL REFERENCES research_opportunities(id),
    rank            INTEGER NOT NULL,
    UNIQUE (cache_id, rank)
);


-- ═══════════════════════════════════════════════════════════════════════
--  FULL PLATFORM TABLES  (Phase 2+, not yet used by application code)
-- ═══════════════════════════════════════════════════════════════════════

-- NOTE: The tables below use UUID primary keys and the extended column
--       set from the technical design doc.  They will be activated
--       when the corresponding application code is written.
--       To apply them now, uncomment the block below.

/*
CREATE TABLE IF NOT EXISTS universities_full (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,
    domain      TEXT,
    country     TEXT NOT NULL,
    state       TEXT,
    city        TEXT,
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION,
    tier        TEXT CHECK (tier IN ('r1', 'r2', 'other')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS departments (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities_full(id),
    name          TEXT NOT NULL,
    url           TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (university_id, name)
);

CREATE TABLE IF NOT EXISTS professors_full (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    email           TEXT,
    department_id   UUID NOT NULL REFERENCES departments(id),
    title           TEXT,
    profile_url     TEXT,
    scholar_url     TEXT,
    orcid           TEXT,
    bio             TEXT,
    mentorship_style TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_professors_full_dept ON professors_full(department_id);

CREATE TABLE IF NOT EXISTS labs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    professor_id    UUID NOT NULL REFERENCES professors_full(id),
    name            TEXT NOT NULL,
    description     TEXT,
    website_url     TEXT,
    lab_size        INTEGER,
    funding_sources TEXT[],
    facilities      TEXT[],
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_labs_professor ON labs(professor_id);

CREATE TABLE IF NOT EXISTS research_areas (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name      TEXT NOT NULL UNIQUE,
    parent_id UUID REFERENCES research_areas(id)
);

CREATE TABLE IF NOT EXISTS lab_research_areas (
    lab_id           UUID NOT NULL REFERENCES labs(id),
    research_area_id UUID NOT NULL REFERENCES research_areas(id),
    PRIMARY KEY (lab_id, research_area_id)
);

CREATE TABLE IF NOT EXISTS hiring_signals (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lab_id      UUID NOT NULL REFERENCES labs(id),
    source      TEXT NOT NULL CHECK (source IN ('website', 'grant', 'social', 'publication', 'manual')),
    signal_type TEXT NOT NULL,
    raw_text    TEXT,
    url         TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ,
    confidence  REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    reviewed    BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS idx_hiring_signals_lab ON hiring_signals(lab_id, detected_at DESC);

CREATE TABLE IF NOT EXISTS hiring_status (
    lab_id         UUID PRIMARY KEY REFERENCES labs(id),
    status         TEXT NOT NULL CHECK (status IN ('actively_hiring', 'might_hire', 'not_hiring', 'unknown')),
    score          REAL NOT NULL CHECK (score BETWEEN 0 AND 100),
    confidence     REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    last_signal_at TIMESTAMPTZ,
    computed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS publications (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lab_id     UUID NOT NULL REFERENCES labs(id),
    title      TEXT NOT NULL,
    venue      TEXT,
    year       INTEGER,
    doi        TEXT,
    url        TEXT,
    abstract   TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS students (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL UNIQUE,
    academic_level  TEXT NOT NULL CHECK (academic_level IN ('undergraduate', 'masters', 'phd', 'postdoc')),
    university      TEXT,
    major           TEXT,
    gpa             REAL,
    graduation_date DATE,
    bio             TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS student_skills (
    student_id UUID NOT NULL REFERENCES students(id),
    skill_name TEXT NOT NULL,
    level      TEXT NOT NULL CHECK (level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    years_exp  REAL,
    PRIMARY KEY (student_id, skill_name)
);

CREATE TABLE IF NOT EXISTS student_research_interests (
    student_id       UUID NOT NULL REFERENCES students(id),
    research_area_id UUID NOT NULL REFERENCES research_areas(id),
    PRIMARY KEY (student_id, research_area_id)
);
*/
