# Research Lab/PI Search Engine - Technical Design

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Database Schemas](#database-schemas)
4. [API Design](#api-design)
5. [Search & Ranking](#search--ranking)
6. [Data Pipeline Architecture](#data-pipeline-architecture)
7. [Machine Learning Pipeline](#machine-learning-pipeline)
8. [Caching Strategy](#caching-strategy)
9. [Authentication & Rate Limiting](#authentication--rate-limiting)
10. [Monitoring & Observability](#monitoring--observability)
11. [Deployment & Scaling](#deployment--scaling)
12. [Error Handling & Resilience](#error-handling--resilience)
13. [Testing Strategy](#testing-strategy)

---

## Overview

This document describes the implementation design for TorchMail's Research Lab/PI Search Engine — the core subsystem responsible for discovering, indexing, ranking, and recommending research labs to students. It covers API contracts, data models, ML pipelines, infrastructure, and operational concerns.

### Design Principles
- **Accuracy over speed**: Hiring-intent signals must be validated before surfacing to users.
- **Graceful degradation**: The system falls back to simpler ranking when ML models or enrichment services are unavailable.
- **Privacy by default**: Student data is never shared with labs without explicit consent.
- **Incremental complexity**: Each phase adds capability on top of the previous one; the MVP works without ML.

### Service Boundaries

| Service | Responsibility | Primary Store |
|---------|---------------|---------------|
| `search-api` | Query parsing, ranking, response assembly | Elasticsearch (read) |
| `data-ingest` | Crawling, scraping, API polling | PostgreSQL (write), Elasticsearch (write) |
| `ml-service` | Hiring-intent scoring, compatibility, embeddings | Model registry, feature store |
| `profile-service` | Student & lab profile CRUD | PostgreSQL |
| `recommendation-service` | Personalized lab suggestions | Redis (cache), PostgreSQL |

Services communicate via an internal message bus (NATS / Amazon SQS) for async events and gRPC for synchronous calls within the cluster. The public API is exposed through an API gateway (Kong or AWS API Gateway) that handles TLS termination, JWT validation, and rate limiting.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          API Gateway                                │
│              (Kong / AWS ALB — TLS, JWT, rate-limit)                │
└─────────┬──────────────┬──────────────┬──────────────┬──────────────┘
          │              │              │              │
   ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐ ┌────▼──────────┐
   │ search-api  │ │ profile  │ │ recommend  │ │  data-ingest  │
   │  (FastAPI)  │ │ service  │ │  service   │ │   (workers)   │
   └──────┬──────┘ └────┬─────┘ └─────┬──────┘ └────┬──────────┘
          │              │              │              │
   ┌──────▼──────┐      │         ┌────▼────┐   ┌────▼─────┐
   │Elasticsearch│      │         │  Redis  │   │  NATS /  │
   │  (search)   │◄─────┼─────────┤ (cache) │   │   SQS    │
   └─────────────┘      │         └─────────┘   └──────────┘
                   ┌────▼─────┐
                   │PostgreSQL│
                   │ (source  │
                   │ of truth)│
                   └──────────┘
```

---

## Database Schemas

### PostgreSQL — Relational Source of Truth

```sql
-- Core lab/professor tables

CREATE TABLE universities (
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

CREATE TABLE departments (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id),
    name          TEXT NOT NULL,
    url           TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (university_id, name)
);

CREATE TABLE professors (
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
CREATE INDEX idx_professors_department ON professors(department_id);

CREATE TABLE labs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    professor_id    UUID NOT NULL REFERENCES professors(id),
    name            TEXT NOT NULL,
    description     TEXT,
    website_url     TEXT,
    lab_size        INT,
    funding_sources TEXT[],
    facilities      TEXT[],
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_labs_professor ON labs(professor_id);

CREATE TABLE research_areas (
    id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name  TEXT NOT NULL UNIQUE,
    parent_id UUID REFERENCES research_areas(id)
);

CREATE TABLE lab_research_areas (
    lab_id          UUID NOT NULL REFERENCES labs(id),
    research_area_id UUID NOT NULL REFERENCES research_areas(id),
    PRIMARY KEY (lab_id, research_area_id)
);

CREATE TABLE hiring_signals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lab_id          UUID NOT NULL REFERENCES labs(id),
    source          TEXT NOT NULL CHECK (source IN ('website', 'grant', 'social', 'publication', 'manual')),
    signal_type     TEXT NOT NULL,
    raw_text        TEXT,
    url             TEXT,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ,
    confidence      REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    reviewed        BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX idx_hiring_signals_lab ON hiring_signals(lab_id, detected_at DESC);

CREATE TABLE hiring_status (
    lab_id          UUID PRIMARY KEY REFERENCES labs(id),
    status          TEXT NOT NULL CHECK (status IN ('actively_hiring', 'might_hire', 'not_hiring', 'unknown')),
    score           REAL NOT NULL CHECK (score BETWEEN 0 AND 100),
    confidence      REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    last_signal_at  TIMESTAMPTZ,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE publications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lab_id      UUID NOT NULL REFERENCES labs(id),
    title       TEXT NOT NULL,
    venue       TEXT,
    year        INT,
    doi         TEXT,
    url         TEXT,
    abstract    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Student profile tables

CREATE TABLE students (
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

CREATE TABLE student_skills (
    student_id  UUID NOT NULL REFERENCES students(id),
    skill_name  TEXT NOT NULL,
    level       TEXT NOT NULL CHECK (level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    years_exp   REAL,
    PRIMARY KEY (student_id, skill_name)
);

CREATE TABLE student_research_interests (
    student_id       UUID NOT NULL REFERENCES students(id),
    research_area_id UUID NOT NULL REFERENCES research_areas(id),
    PRIMARY KEY (student_id, research_area_id)
);
```

### Elasticsearch — Search Index Mapping

```json
{
  "mappings": {
    "properties": {
      "lab_id":            { "type": "keyword" },
      "lab_name":          { "type": "text", "analyzer": "english", "fields": { "raw": { "type": "keyword" } } },
      "professor_name":    { "type": "text", "fields": { "raw": { "type": "keyword" } } },
      "university":        { "type": "text", "fields": { "raw": { "type": "keyword" } } },
      "department":        { "type": "text", "fields": { "raw": { "type": "keyword" } } },
      "research_areas":    { "type": "text", "analyzer": "english", "fields": { "raw": { "type": "keyword" } } },
      "description":       { "type": "text", "analyzer": "english" },
      "skills_required":   { "type": "keyword" },
      "hiring_status":     { "type": "keyword" },
      "hiring_score":      { "type": "float" },
      "hiring_confidence": { "type": "float" },
      "lab_size":          { "type": "integer" },
      "publication_count": { "type": "integer" },
      "grant_funding":     { "type": "float" },
      "location":          { "type": "geo_point" },
      "application_deadline": { "type": "date" },
      "embedding":         { "type": "dense_vector", "dims": 768, "index": true, "similarity": "cosine" },
      "last_updated":      { "type": "date" },
      "boost_factor":      { "type": "float" },
      "recent_hiring_change":     { "type": "boolean" },
      "hiring_change_timestamp":  { "type": "date" }
    }
  },
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "research_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "research_synonyms", "english_stemmer"]
        }
      },
      "filter": {
        "research_synonyms": {
          "type": "synonym",
          "synonyms": [
            "ml, machine learning",
            "nlp, natural language processing",
            "cv, computer vision",
            "dl, deep learning",
            "rl, reinforcement learning",
            "hci, human computer interaction"
          ]
        },
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        }
      }
    }
  }
}
```

---

## API Design

All endpoints are versioned under `/api/v1`. Responses use a standard envelope:

```typescript
interface ApiEnvelope<T> {
  ok: boolean;
  data?: T;
  error?: { code: string; message: string; details?: unknown };
  meta?: { request_id: string; timestamp: string };
}
```

### Search API

```typescript
// POST /api/v1/search/labs
interface SearchRequest {
  query?: string;
  filters?: SearchFilters;
  sort_by?: 'relevance' | 'hiring_score' | 'compatibility' | 'recently_updated';
  page?: number;   // default 1
  limit?: number;  // default 20, max 100
  include_personalized?: boolean;
}

interface SearchFilters {
  university?: string[];
  department?: string[];
  research_area?: string[];
  hiring_status?: HiringStatusEnum[];
  min_hiring_score?: number;     // 0-100
  lab_size?: { min?: number; max?: number };
  location?: {
    latitude: number;
    longitude: number;
    radius_km: number;
  };
  application_deadline?: {
    before?: string;  // ISO 8601 date
    after?: string;
  };
  skills_required?: string[];
  international_friendly?: boolean;
  remote_possible?: boolean;
}

type HiringStatusEnum = 'actively_hiring' | 'might_hire' | 'not_hiring';

interface SearchResponse {
  total: number;
  page: number;
  limit: number;
  results: LabResult[];
  facets: SearchFacets;
  query_time_ms: number;
  suggestions?: SearchSuggestion[];
}

interface LabResult {
  id: string;
  name: string;
  professor: {
    id: string;
    name: string;
    title: string;
  };
  university: string;
  department: string;
  research_areas: string[];
  description_snippet: string;   // highlighted excerpt
  hiring_status: HiringStatusEnum;
  hiring_score: number;
  hiring_confidence: number;
  lab_size: number | null;
  location: {
    city: string;
    state: string;
    country: string;
    coordinates?: { lat: number; lon: number };
  };
  compatibility_score?: number;       // present when include_personalized=true
  match_explanation?: string;
  application_deadline?: string;
  last_updated: string;
}

interface SearchFacets {
  universities: FacetBucket[];
  departments: FacetBucket[];
  research_areas: FacetBucket[];
  hiring_status: FacetBucket[];
}

interface FacetBucket {
  key: string;
  doc_count: number;
}

interface SearchSuggestion {
  text: string;
  type: 'query' | 'filter' | 'spelling';
}
```

### Autocomplete / Suggestions API

```typescript
// GET /api/v1/search/suggestions?q={query}&limit=8
interface SuggestionResponse {
  queries: string[];                   // previous popular queries
  labs: LabSuggestionItem[];           // quick lab name matches
  research_areas: string[];            // matching research area taxonomy terms
}

interface LabSuggestionItem {
  id: string;
  name: string;
  professor_name: string;
  university: string;
}
```

### Recommendation API

```typescript
// GET /api/v1/recommendations?limit=20&diversity=0.3&explain=true
interface RecommendationResponse {
  recommendations: Recommendation[];
  profile_completeness: number;  // 0-100
  skill_gaps: SkillGap[];
}

interface Recommendation {
  lab: LabResult;
  compatibility: CompatibilityBreakdown;
  success_prediction: SuccessPrediction;
  priority: 'high' | 'medium' | 'low';
  explanation: string;
}

interface CompatibilityBreakdown {
  total: number;      // 0-100
  skills: number;     // 0-100, weight 40%
  research: number;   // 0-100, weight 30%
  timing: number;     // 0-100, weight 20%
  cultural: number;   // 0-100, weight 10%
}

interface SuccessPrediction {
  interview_probability: number;       // 0-1
  acceptance_probability: number;      // 0-1
  expected_response_days: number;
  confidence: number;                  // 0-1
}

interface SkillGap {
  skill: string;
  current_level: string | null;
  recommended_level: string;
  labs_requiring: number;
}
```

### Lab Profile API

```typescript
// GET /api/v1/labs/:id
interface LabProfileResponse {
  lab: DetailedLabProfile;
  hiring_timeline: HiringEvent[];
  current_projects: ResearchProject[];
  team_members: TeamMember[];
  recent_publications: Publication[];
  application_process: ApplicationProcess;
  compatibility?: CompatibilityBreakdown;
  similar_labs: SimilarLabItem[];
}

interface DetailedLabProfile {
  id: string;
  name: string;
  professor: {
    id: string;
    name: string;
    title: string;
    email?: string;
    profile_url?: string;
    scholar_url?: string;
  };
  university: { name: string; city: string; state: string; country: string };
  department: string;
  research_areas: string[];
  description: string;
  mentorship_style: string | null;
  funding_sources: string[];
  facilities: string[];
  lab_size: number | null;
  hiring: {
    status: HiringStatusEnum;
    score: number;
    confidence: number;
    needs: HiringNeed[];
    deadlines: ApplicationDeadline[];
  };
  website_url: string | null;
  last_updated: string;
}

interface HiringNeed {
  role: string;                 // e.g. "PhD Student", "Postdoc", "Research Intern"
  skills: string[];
  description: string;
  deadline?: string;
}

interface ApplicationDeadline {
  label: string;
  date: string;
  rolling: boolean;
}

interface HiringEvent {
  date: string;
  event: string;     // e.g. "Posted opening", "Received grant"
  source: string;
}

interface ResearchProject {
  title: string;
  description: string;
  status: 'active' | 'completed';
  skills: string[];
}

interface TeamMember {
  name: string;
  role: string;
  joined_year: number | null;
}

interface Publication {
  title: string;
  venue: string;
  year: number;
  url?: string;
}

interface ApplicationProcess {
  method: string;                // e.g. "email", "portal", "both"
  instructions: string | null;
  required_documents: string[];
  tips: string[];
}

interface SimilarLabItem {
  id: string;
  name: string;
  university: string;
  hiring_score: number;
  similarity_reason: string;
}
```

### Student Profile API

```typescript
// POST /api/v1/students/profile
interface StudentProfileRequest {
  academic_level: 'undergraduate' | 'masters' | 'phd' | 'postdoc';
  gpa?: number;
  university: string;
  major: string;
  graduation_date: string;
  skills: SkillEntry[];
  research_interests: string[];
  previous_research?: ResearchExperience[];
  career_goals?: string[];
  availability: {
    start_date: string;
    end_date?: string;
    hours_per_week: number;
  };
  preferences: {
    location_preferences?: string[];
    lab_size_preference?: 'small' | 'medium' | 'large' | 'any';
    funding_required?: boolean;
    remote_ok?: boolean;
  };
}

interface SkillEntry {
  name: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  years_experience?: number;
}

interface ResearchExperience {
  title: string;
  lab_or_org: string;
  duration_months: number;
  description: string;
  skills_used: string[];
}

// Response
interface StudentProfileResponse {
  profile_id: string;
  completeness_score: number;          // 0-100
  improvement_tips: string[];
  match_statistics: {
    total_compatible_labs: number;
    top_research_areas: string[];
  };
}
```

---

## Search & Ranking

### Query Pipeline

Every search request flows through a multi-stage pipeline:

1. **Query Understanding** — Tokenize, spell-correct, extract entities (university names, research areas), detect intent ("labs hiring in NLP at Stanford").
2. **Query Expansion** — Add synonyms and related terms via the synonym filter and, for Phase 3+, an embedding-based expansion.
3. **Retrieval** — Elasticsearch multi-match query across `lab_name`, `professor_name`, `research_areas`, `description`, `skills_required`.
4. **Re-ranking** — Apply a weighted scoring formula (see below) on the candidate set.
5. **Personalization** (optional) — If the caller is authenticated and `include_personalized=true`, overlay compatibility scores from the ML service.
6. **Response Assembly** — Build facets, add highlights, attach suggestions.

### Elasticsearch Query Construction

```python
def build_es_query(req: SearchRequest, student_embedding=None) -> dict:
    must_clauses = []
    filter_clauses = []
    should_clauses = []

    if req.query:
        must_clauses.append({
            "multi_match": {
                "query": req.query,
                "fields": [
                    "lab_name^3",
                    "professor_name^2",
                    "research_areas^2.5",
                    "description",
                    "skills_required^1.5"
                ],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        })

    if req.filters:
        f = req.filters
        if f.university:
            filter_clauses.append({"terms": {"university.raw": f.university}})
        if f.department:
            filter_clauses.append({"terms": {"department.raw": f.department}})
        if f.research_area:
            filter_clauses.append({"terms": {"research_areas.raw": f.research_area}})
        if f.hiring_status:
            filter_clauses.append({"terms": {"hiring_status": f.hiring_status}})
        if f.min_hiring_score is not None:
            filter_clauses.append({"range": {"hiring_score": {"gte": f.min_hiring_score}}})
        if f.lab_size:
            size_range = {}
            if f.lab_size.get("min") is not None:
                size_range["gte"] = f.lab_size["min"]
            if f.lab_size.get("max") is not None:
                size_range["lte"] = f.lab_size["max"]
            filter_clauses.append({"range": {"lab_size": size_range}})
        if f.location:
            filter_clauses.append({
                "geo_distance": {
                    "distance": f"{f.location['radius_km']}km",
                    "location": {
                        "lat": f.location["latitude"],
                        "lon": f.location["longitude"]
                    }
                }
            })
        if f.application_deadline:
            dl_range = {}
            if f.application_deadline.get("after"):
                dl_range["gte"] = f.application_deadline["after"]
            if f.application_deadline.get("before"):
                dl_range["lte"] = f.application_deadline["before"]
            filter_clauses.append({"range": {"application_deadline": dl_range}})

    # Boost recently-updated and actively-hiring labs
    should_clauses.append({
        "range": {
            "last_updated": {
                "gte": "now-7d/d",
                "boost": 1.5
            }
        }
    })
    should_clauses.append({
        "term": {
            "hiring_status": {
                "value": "actively_hiring",
                "boost": 2.0
            }
        }
    })

    body: dict = {
        "query": {
            "bool": {
                "must": must_clauses or [{"match_all": {}}],
                "filter": filter_clauses,
                "should": should_clauses
            }
        },
        "highlight": {
            "fields": {
                "description": {"fragment_size": 150, "number_of_fragments": 1}
            }
        },
        "aggs": {
            "universities": {"terms": {"field": "university.raw", "size": 30}},
            "departments":  {"terms": {"field": "department.raw", "size": 30}},
            "research_areas": {"terms": {"field": "research_areas.raw", "size": 30}},
            "hiring_status": {"terms": {"field": "hiring_status", "size": 5}}
        }
    }

    # Semantic re-ranking (Phase 3+): kNN on embedding field
    if student_embedding is not None:
        body["knn"] = {
            "field": "embedding",
            "query_vector": student_embedding,
            "k": 50,
            "num_candidates": 200
        }

    return body
```

### Ranking Formula

The final ranking score combines text relevance, hiring signal strength, and freshness:

```
score = (0.40 * text_relevance)
      + (0.30 * hiring_score / 100)
      + (0.15 * freshness_decay)
      + (0.15 * compatibility_score / 100)   // 0 when not personalized
```

Where:
- `text_relevance` is the normalized Elasticsearch BM25 score.
- `hiring_score` is the ML-derived 0-100 hiring intent score.
- `freshness_decay = exp(-0.05 * days_since_update)` — exponential decay so stale results sink.
- `compatibility_score` is the ML compatibility model output (0-100), zero-filled for anonymous users.

---

## Data Pipeline Architecture

### Pipeline Orchestration

The data pipeline runs as a set of independent workers coordinated by a task queue. Each worker type has its own concurrency limit and retry policy.

```python
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SignalSource(Enum):
    WEBSITE = "website"
    GRANT = "grant"
    SOCIAL = "social"
    PUBLICATION = "publication"
    MANUAL = "manual"


@dataclass
class PipelineConfig:
    poll_interval_seconds: int = 300
    max_concurrent_collectors: int = 4
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_seconds: int = 120
    batch_size: int = 50


@dataclass
class CollectorHealth:
    consecutive_failures: int = 0
    last_failure_at: datetime | None = None
    is_open: bool = False  # circuit breaker state

    def record_failure(self, reset_seconds: int):
        self.consecutive_failures += 1
        self.last_failure_at = datetime.utcnow()

    def record_success(self):
        self.consecutive_failures = 0
        self.is_open = False

    def should_skip(self, threshold: int, reset_seconds: int) -> bool:
        if not self.is_open:
            if self.consecutive_failures >= threshold:
                self.is_open = True
            return False
        if self.last_failure_at and (
            datetime.utcnow() - self.last_failure_at > timedelta(seconds=reset_seconds)
        ):
            self.is_open = False
            return False
        return True


class DataPipeline:
    """Orchestrates data collection, processing, validation, and indexing."""

    def __init__(self, collectors: dict, processors: dict, storage, config: PipelineConfig | None = None):
        self.collectors = collectors
        self.processors = processors
        self.storage = storage
        self.config = config or PipelineConfig()
        self._health: dict[str, CollectorHealth] = {
            name: CollectorHealth() for name in collectors
        }
        self._shutdown = asyncio.Event()

    async def run(self):
        """Main loop. Call shutdown() to stop gracefully."""
        logger.info("Data pipeline started (interval=%ds)", self.config.poll_interval_seconds)
        while not self._shutdown.is_set():
            cycle_start = datetime.utcnow()
            try:
                raw = await self._collect_all()
                processed = await self._process(raw)
                validated = await self._validate(processed)
                await self._store_and_index(validated)
            except Exception:
                logger.exception("Unhandled error in pipeline cycle")
            elapsed = (datetime.utcnow() - cycle_start).total_seconds()
            sleep_for = max(0, self.config.poll_interval_seconds - elapsed)
            try:
                await asyncio.wait_for(self._shutdown.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                pass
        logger.info("Data pipeline shut down")

    def shutdown(self):
        self._shutdown.set()

    async def _collect_all(self) -> dict:
        sem = asyncio.Semaphore(self.config.max_concurrent_collectors)
        results = {}

        async def _run_collector(name, collector):
            health = self._health[name]
            if health.should_skip(
                self.config.circuit_breaker_threshold,
                self.config.circuit_breaker_reset_seconds
            ):
                logger.warning("Skipping collector %s (circuit breaker open)", name)
                return

            async with sem:
                for attempt in range(1, self.config.max_retries + 1):
                    try:
                        data = await collector.collect()
                        health.record_success()
                        results[name] = data
                        return
                    except Exception:
                        wait = self.config.retry_backoff_base ** attempt
                        logger.warning(
                            "Collector %s attempt %d/%d failed, retrying in %.1fs",
                            name, attempt, self.config.max_retries, wait,
                            exc_info=True,
                        )
                        health.record_failure(self.config.circuit_breaker_reset_seconds)
                        if attempt < self.config.max_retries:
                            await asyncio.sleep(wait)

                logger.error("Collector %s exhausted retries", name)

        await asyncio.gather(
            *(_run_collector(n, c) for n, c in self.collectors.items())
        )
        return results

    async def _process(self, raw: dict) -> list:
        all_items = []
        for source_name, items in raw.items():
            for item in items:
                for proc in self.processors.values():
                    item = await proc.process(item)
                all_items.append(item)
        return all_items

    async def _validate(self, items: list) -> list:
        valid = []
        for item in items:
            if item.get("_valid", True):
                valid.append(item)
            else:
                logger.debug("Dropped invalid item: %s", item.get("id"))
        return valid

    async def _store_and_index(self, items: list) -> None:
        for batch_start in range(0, len(items), self.config.batch_size):
            batch = items[batch_start : batch_start + self.config.batch_size]
            await self.storage.upsert_batch(batch)
```

### Search Index Updater

```python
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ChangeSet:
    significant: bool
    hiring_status_changed: bool = False
    detected_at: datetime | None = None
    changed_fields: list[str] = field(default_factory=list)


class IndexUpdater:
    """Keeps the Elasticsearch index in sync with PostgreSQL."""

    def __init__(self, es_client, change_detector, batch_size: int = 100):
        self.es = es_client
        self.change_detector = change_detector
        self.batch_size = batch_size

    async def sync_lab(self, lab_data) -> None:
        changes = await self.change_detector.detect_changes(lab_data)

        if not changes.significant:
            await self.es.update(
                index="labs",
                id=lab_data.id,
                body={"doc": {"last_updated": datetime.utcnow().isoformat()}},
            )
            return

        doc = self._build_document(lab_data, changes)
        await self.es.index(index="labs", id=lab_data.id, body=doc)

    async def bulk_sync(self, lab_data_list: list) -> dict:
        """Bulk-index a batch of labs. Returns counts of success/failure."""
        actions = []
        for lab_data in lab_data_list:
            changes = await self.change_detector.detect_changes(lab_data)
            doc = self._build_document(lab_data, changes)
            actions.append({"index": {"_index": "labs", "_id": lab_data.id}})
            actions.append(doc)

        if not actions:
            return {"indexed": 0, "errors": 0}

        resp = await self.es.bulk(body=actions, refresh="wait_for")
        error_count = sum(1 for item in resp["items"] if item["index"].get("error"))
        return {"indexed": len(lab_data_list) - error_count, "errors": error_count}

    def _build_document(self, lab_data, changes: ChangeSet) -> dict:
        doc = {
            "lab_id": lab_data.id,
            "lab_name": lab_data.name,
            "professor_name": lab_data.professor_name,
            "university": lab_data.university,
            "department": lab_data.department,
            "research_areas": lab_data.research_areas,
            "description": lab_data.description,
            "hiring_status": lab_data.hiring_status,
            "hiring_score": lab_data.hiring_score,
            "hiring_confidence": lab_data.hiring_confidence,
            "lab_size": lab_data.lab_size,
            "publication_count": lab_data.publication_count,
            "grant_funding": lab_data.grant_funding,
            "skills_required": lab_data.skills_required,
            "application_deadline": lab_data.application_deadline,
            "location": {"lat": lab_data.lat, "lon": lab_data.lon},
            "embedding": lab_data.embedding,
            "last_updated": datetime.utcnow().isoformat(),
            "boost_factor": self._calculate_boost(lab_data, changes),
            "recent_hiring_change": changes.hiring_status_changed,
        }
        if changes.hiring_status_changed:
            doc["hiring_change_timestamp"] = changes.detected_at.isoformat()
        return doc

    @staticmethod
    def _calculate_boost(lab_data, changes: ChangeSet) -> float:
        boost = 1.0
        if changes.hiring_status_changed:
            boost += 0.5
        if lab_data.hiring_status == "actively_hiring":
            boost += 0.3
        return boost
```

---

## Machine Learning Pipeline

### Overview

Three models are trained and served:

| Model | Task | Input | Output | Retraining Cadence |
|-------|------|-------|--------|-------------------|
| Hiring Intent | Binary classification | Lab features (text, temporal, structural) | `is_hiring` probability + confidence | Weekly |
| Compatibility | Regression | Student-lab feature pairs | Compatibility score 0-100 | Biweekly |
| Success Prediction | Regression | Application features | Interview/acceptance probability | Monthly |

All models are served behind the `ml-service` gRPC API. The search-api calls ml-service synchronously for compatibility scoring and asynchronously (pre-computed) for hiring intent.

### Feature Engineering

```python
import numpy as np
from dataclasses import dataclass

@dataclass
class LabFeatures:
    # Text-based
    hiring_keyword_density: float     # fraction of page tokens that are hiring keywords
    positive_sentiment_score: float
    openings_page_exists: bool

    # Temporal
    website_update_recency_days: int
    publication_count_last_year: int
    grant_award_recency_days: int | None
    social_post_count_last_90d: int

    # Structural
    lab_size: int
    phd_student_count: int | None
    has_funding: bool
    international_students: bool

    def to_array(self) -> np.ndarray:
        return np.array([
            self.hiring_keyword_density,
            self.positive_sentiment_score,
            float(self.openings_page_exists),
            min(self.website_update_recency_days, 365) / 365.0,
            min(self.publication_count_last_year, 50) / 50.0,
            min(self.grant_award_recency_days or 730, 730) / 730.0,
            min(self.social_post_count_last_90d, 100) / 100.0,
            min(self.lab_size, 50) / 50.0,
            min(self.phd_student_count or 0, 20) / 20.0,
            float(self.has_funding),
            float(self.international_students),
        ], dtype=np.float32)


@dataclass
class CompatibilityFeatures:
    skill_overlap_ratio: float          # Jaccard similarity of skills
    research_embedding_cosine: float    # cosine sim of student vs lab embeddings
    timing_overlap_days: int            # overlap between availability and hiring window
    lab_size_preference_match: bool
    location_match: bool
    academic_level_match: bool
    gpa_percentile: float | None

    def to_array(self) -> np.ndarray:
        return np.array([
            self.skill_overlap_ratio,
            self.research_embedding_cosine,
            min(self.timing_overlap_days, 365) / 365.0,
            float(self.lab_size_preference_match),
            float(self.location_match),
            float(self.academic_level_match),
            self.gpa_percentile if self.gpa_percentile is not None else 0.5,
        ], dtype=np.float32)
```

### Model Training

```python
import logging
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    mean_absolute_error, r2_score
)
import numpy as np
import joblib

logger = logging.getLogger(__name__)


class HiringIntentTrainer:
    """Trains and evaluates the hiring-intent binary classifier."""

    def __init__(self, model_registry):
        self.registry = model_registry

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )),
        ])

        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
        logger.info("Hiring-intent CV ROC-AUC: %.4f ± %.4f", cv_scores.mean(), cv_scores.std())

        pipeline.fit(X, y)

        metrics = {
            "cv_roc_auc_mean": float(cv_scores.mean()),
            "cv_roc_auc_std": float(cv_scores.std()),
        }

        current_best = self.registry.get_latest_metrics("hiring_intent")
        if current_best is None or metrics["cv_roc_auc_mean"] > current_best.get("cv_roc_auc_mean", 0):
            self.registry.register(
                model_name="hiring_intent",
                model=pipeline,
                metrics=metrics,
            )
            logger.info("Registered new hiring-intent model (AUC=%.4f)", metrics["cv_roc_auc_mean"])
        else:
            logger.info("New model (AUC=%.4f) did not beat current (AUC=%.4f); skipping registration",
                        metrics["cv_roc_auc_mean"], current_best["cv_roc_auc_mean"])

        return metrics


class CompatibilityTrainer:
    """Trains the student-lab compatibility regression model."""

    def __init__(self, model_registry):
        self.registry = model_registry

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("reg", GradientBoostingRegressor(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )),
        ])

        from sklearn.model_selection import KFold
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="r2")
        logger.info("Compatibility CV R²: %.4f ± %.4f", cv_scores.mean(), cv_scores.std())

        pipeline.fit(X, y)

        metrics = {
            "cv_r2_mean": float(cv_scores.mean()),
            "cv_r2_std": float(cv_scores.std()),
        }

        current_best = self.registry.get_latest_metrics("compatibility")
        if current_best is None or metrics["cv_r2_mean"] > current_best.get("cv_r2_mean", 0):
            self.registry.register(
                model_name="compatibility",
                model=pipeline,
                metrics=metrics,
            )

        return metrics
```

### Model Serving

Models are loaded from the registry at startup and cached in memory. A background task checks for new model versions every 5 minutes.

```python
class ModelServer:
    """Loads trained models from the registry and serves predictions."""

    def __init__(self, model_registry):
        self.registry = model_registry
        self._models: dict[str, Pipeline] = {}
        self._versions: dict[str, str] = {}

    async def load_models(self):
        for name in ["hiring_intent", "compatibility", "success_prediction"]:
            model, version = self.registry.get_latest(name)
            if model is not None:
                self._models[name] = model
                self._versions[name] = version
                logger.info("Loaded model %s (version=%s)", name, version)

    def predict_hiring_intent(self, features: np.ndarray) -> dict:
        model = self._models.get("hiring_intent")
        if model is None:
            return {"probability": None, "confidence": 0.0, "model_available": False}
        proba = model.predict_proba(features.reshape(1, -1))[0]
        return {
            "probability": float(proba[1]),
            "confidence": float(max(proba)),
            "model_available": True,
        }

    def predict_compatibility(self, features: np.ndarray) -> float | None:
        model = self._models.get("compatibility")
        if model is None:
            return None
        score = model.predict(features.reshape(1, -1))[0]
        return float(np.clip(score, 0, 100))
```

---

## Caching Strategy

| Cache Layer | Store | TTL | Invalidation |
|------------|-------|-----|-------------|
| Search results (anonymous) | Redis | 5 min | On index refresh |
| Search results (personalized) | Not cached | — | — |
| Lab profiles | Redis | 15 min | On lab update event |
| Facet counts | Redis | 10 min | On index refresh |
| Autocomplete suggestions | Redis | 30 min | Rebuilt nightly |
| Student profile | Redis | 60 min | On profile update |
| ML model predictions (hiring) | Redis | 24 h | On model retrain |

Cache keys follow the pattern `torchmail:{service}:{entity}:{hash}`, e.g. `torchmail:search:results:sha256(query+filters)`.

Personalized search results are **not** cached because the compatibility overlay varies per student. Instead, the base search result set is cached and compatibility scores are computed and merged at response time.

---

## Authentication & Rate Limiting

### Authentication

- Public endpoints (search, autocomplete, lab profile view): No auth required; limited to lower rate tier.
- Personalized endpoints (recommendations, compatibility): Require a valid JWT (`Authorization: Bearer <token>`).
- Write endpoints (student profile CRUD): Require JWT with `student` role.
- Admin endpoints (manual data curation, model management): Require JWT with `admin` role.

JWT validation is performed at the API gateway layer. The gateway injects `X-User-Id` and `X-User-Roles` headers into downstream requests.

### Rate Limiting

| Tier | Requests/min | Burst |
|------|-------------|-------|
| Anonymous | 30 | 10 |
| Authenticated (free) | 120 | 30 |
| Authenticated (premium) | 600 | 100 |
| Admin | Unlimited | — |

Rate limiting uses a sliding-window counter in Redis, keyed by IP (anonymous) or user ID (authenticated). HTTP 429 responses include a `Retry-After` header.

---

## Monitoring & Observability

### Metrics (Prometheus)

```python
from prometheus_client import Histogram, Counter, Gauge

SEARCH_LATENCY = Histogram(
    "search_latency_seconds",
    "Search request latency",
    ["endpoint", "status"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

SEARCH_RESULT_COUNT = Histogram(
    "search_result_count",
    "Number of results returned per search",
    buckets=[0, 1, 5, 10, 20, 50, 100],
)

SEARCH_REQUESTS = Counter(
    "search_requests_total",
    "Total search requests",
    ["has_query", "has_filters", "personalized"],
)

HIRING_SCORE_DISTRIBUTION = Histogram(
    "hiring_score",
    "Distribution of hiring scores across indexed labs",
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)

INDEX_STALENESS_HOURS = Gauge(
    "index_staleness_hours",
    "Hours since the oldest lab in the index was updated",
)

PIPELINE_CYCLE_DURATION = Histogram(
    "pipeline_cycle_duration_seconds",
    "Duration of each data pipeline cycle",
    buckets=[10, 30, 60, 120, 300, 600],
)

MODEL_PREDICTION_LATENCY = Histogram(
    "model_prediction_latency_seconds",
    "Latency of ML model predictions",
    ["model_name"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25],
)
```

### Structured Logging

All services emit JSON-structured logs with the fields: `timestamp`, `level`, `service`, `request_id`, `message`, `extra`. Logs are shipped via Fluent Bit to a centralized store (Elasticsearch / Loki).

### Distributed Tracing

OpenTelemetry is instrumented across all services. Traces propagate the `traceparent` header through gRPC and HTTP calls. Traces are exported to Jaeger for visualization.

### Alerting Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| Search P95 latency > 2s | for 5 min | Warning |
| Search P95 latency > 5s | for 2 min | Critical |
| Pipeline cycle failure | 3 consecutive | Warning |
| Pipeline cycle failure | 5 consecutive | Critical |
| Index staleness > 48h | — | Warning |
| ML model AUC drop > 5% | After retrain | Warning |
| Error rate > 1% | for 5 min | Warning |
| Error rate > 5% | for 2 min | Critical |

### Clickthrough Tracking

```python
class SearchAnalytics:
    """Records user interactions with search results for ranking feedback."""

    def __init__(self, event_store):
        self.events = event_store

    async def record_impression(self, search_id: str, lab_ids: list[str]):
        await self.events.emit("search.impression", {
            "search_id": search_id,
            "lab_ids": lab_ids,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def record_click(self, search_id: str, lab_id: str, position: int):
        await self.events.emit("search.click", {
            "search_id": search_id,
            "lab_id": lab_id,
            "position": position,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def record_save(self, search_id: str, lab_id: str):
        await self.events.emit("search.save", {
            "search_id": search_id,
            "lab_id": lab_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
```

---

## Deployment & Scaling

### Container Images

Each service has its own `Dockerfile` and is built in CI. Images are tagged with the git SHA — **never** `latest` in production.

### Kubernetes Manifests

```yaml
# search-api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-api
  namespace: torchmail
  labels:
    app: search-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: search-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: search-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      containers:
      - name: search-api
        image: ghcr.io/torchmail/search-api:<GIT_SHA>
        ports:
        - name: http
          containerPort: 8080
        - name: metrics
          containerPort: 9090
        env:
        - name: ELASTICSEARCH_URL
          value: "http://elasticsearch.torchmail.svc.cluster.local:9200"
        - name: REDIS_URL
          value: "redis://redis.torchmail.svc.cluster.local:6379/0"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: ML_SERVICE_URL
          value: "ml-service.torchmail.svc.cluster.local:50051"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        readinessProbe:
          httpGet:
            path: /healthz/ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /healthz/live
            port: http
          initialDelaySeconds: 15
          periodSeconds: 20
---
apiVersion: v1
kind: Service
metadata:
  name: search-api
  namespace: torchmail
spec:
  selector:
    app: search-api
  ports:
  - name: http
    port: 80
    targetPort: http
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: search-api
  namespace: torchmail
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: search-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "50"
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: search-api
  namespace: torchmail
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: search-api
```

### Elasticsearch Cluster Sizing

| Phase | Nodes | RAM/Node | Storage/Node | Shards | Replicas |
|-------|-------|----------|-------------|--------|----------|
| MVP (≤1K labs) | 1 | 4 GB | 20 GB SSD | 1 | 0 |
| Phase 2 (≤10K labs) | 2 | 8 GB | 50 GB SSD | 2 | 1 |
| Phase 3 (≤100K labs) | 3 | 16 GB | 100 GB SSD | 3 | 1 |

---

## Error Handling & Resilience

### Failure Modes and Fallbacks

| Failure | Impact | Fallback |
|---------|--------|----------|
| Elasticsearch down | Search unavailable | Return cached results from Redis; show degraded banner |
| ML service down | No compatibility scores | Return results ranked by hiring_score + text relevance only |
| Redis down | Slower responses | Bypass cache; query ES and Postgres directly |
| Data pipeline collector fails | Stale data for that source | Circuit breaker skips collector; other sources continue |
| PostgreSQL down | Profile CRUD unavailable | Return 503; search still works from ES cache |

### Retry & Timeout Policy

- **search-api → Elasticsearch**: 2 retries, 3s timeout per attempt, exponential backoff.
- **search-api → ml-service (gRPC)**: 1 retry, 500ms deadline. On timeout, skip personalization.
- **search-api → Redis**: No retry, 200ms timeout. On failure, treat as cache miss.
- **data-ingest → external websites**: 3 retries, 10s timeout, respect `Retry-After` headers.

### Idempotency

All write operations in the data pipeline are idempotent. Lab upserts use the lab UUID as the deduplication key. Elasticsearch index operations use the lab ID as the document ID, so re-indexing the same data is safe.

---

## Testing Strategy

### Unit Tests
- Feature extraction functions (deterministic input → output).
- Query builder (verify ES query structure for various filter combinations).
- Ranking formula (verify score calculation).
- Cache key generation.

### Integration Tests
- Search API → Elasticsearch (with a test index populated via fixtures).
- Data pipeline → PostgreSQL + Elasticsearch (verify end-to-end flow with a containerized stack).
- ML model serving (load a small test model, verify prediction shapes).

### Load Tests
- Target: sustain 100 req/s at P95 < 2s for the search endpoint.
- Tool: Locust or k6 against a staging environment with representative data.

### ML Model Evaluation
- Offline: k-fold cross-validation with held-out test set; track AUC, precision, recall.
- Online: A/B test new model versions; compare CTR and user satisfaction metrics between model versions.

### Data Quality Tests
- Completeness: >95% of labs have `name`, `university`, `department`, `research_areas`.
- Freshness: >80% of actively-hiring labs updated within the last 7 days.
- Accuracy: Quarterly manual audit of 200 randomly sampled labs.

---

*Document Version: 2.0*
*Last Updated: March 19, 2026*
*Next Review: April 19, 2026*
*Owner: Search Engine Tech Lead*
