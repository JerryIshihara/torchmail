# Research Lab/PI Search Engine — Executive Summary

## The Core Competitive Advantage

The Research Lab/PI Search Engine transforms TorchMail from a static academic directory into an intelligent platform that solves the fundamental **information asymmetry** in academic hiring: students don't know which labs are hiring, and professors can't efficiently reach qualified candidates.

## How It Differs from Existing Solutions

| | Traditional Academic Directories | TorchMail Search Engine |
|---|---|---|
| Hiring data | None — static list of all professors | **Dynamic hiring-intent detection** from multiple signals |
| Matching | Manual keyword search | **ML-powered compatibility scoring** across skills, research, timing, culture |
| Timing | No guidance | **Temporal intelligence** — understands academic cycles, grant timelines |
| Actionability | Information only | **Clear next steps** — application instructions, preparation tips, deadline tracking |
| Effort | 20+ hours of manual research | < 30 seconds to first relevant result |

## Key Innovations

### 1. Real-Time Hiring-Intent Detection

Multiple signal sources — lab websites, publications, grants, social media — are continuously monitored. An ML classifier produces a hiring probability (0–100) with a confidence score. The system learns from application outcomes to improve over time.

### 2. Multi-Dimensional Compatibility Scoring

Each student-lab pair receives a composite compatibility score:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Technical Skills | 40% | Overlap between student skills and lab requirements |
| Research Alignment | 30% | Embedding similarity of student interests and lab focus |
| Timing Compatibility | 20% | Overlap of availability window and hiring window |
| Cultural Fit | 10% | Lab environment and mentorship-style alignment |

### 3. Personalized Recommendations

Rather than a flat ranked list, students receive categorized suggestions:

- **Best Matches** (top 5) — highest compatibility + active hiring.
- **Good Alternatives** (5) — strong in different dimensions.
- **Stretch Opportunities** (5) — ambitious but growth-oriented.
- **Safety Options** (5) — higher acceptance probability.

### 4. Success Prediction & Strategy

For each lab, the system estimates interview probability, expected response time, and competitive positioning, along with specific preparation steps the student can take to improve their chances.

## Technical Architecture at a Glance

### Services

| Service | Role |
|---------|------|
| `search-api` | Query parsing, ranking, response assembly (FastAPI) |
| `data-ingest` | Web crawling, API polling, data enrichment (async workers) |
| `ml-service` | Hiring-intent scoring, compatibility, embeddings (gRPC) |
| `profile-service` | Student and lab profile CRUD |
| `recommendation-service` | Personalized lab suggestions |

### Data Stores

| Store | Purpose |
|-------|---------|
| **Elasticsearch** | Full-text + semantic search, faceted filtering, geo queries |
| **PostgreSQL** | Relational source of truth for all structured data |
| **Redis** | Caching, rate limiting, session data |
| **S3** | Document storage and data archival |

### ML Models

| Model | Task | Retraining |
|-------|------|-----------|
| Hiring Intent | Binary classification — is the lab hiring? | Weekly |
| Compatibility | Regression — student-lab fit score (0–100) | Biweekly |
| Success Prediction | Regression — interview/acceptance probability | Monthly |

## Data Sources & Coverage Targets (Year 1)

| Source | Update Cadence |
|--------|---------------|
| University / lab websites | Daily crawl |
| Research databases (Semantic Scholar, arXiv, PubMed) | Weekly |
| Grant databases (NSF, NIH) | Weekly |
| Social / professional networks | Daily (rate-limited) |

| Coverage Target | Goal |
|----------------|------|
| Top 100 US R1 universities | 100% |
| Total indexed labs | 50,000+ |
| Hiring-intent accuracy | > 90% |
| Daily-updated high-priority labs | 100% |

## User Experience Flow

1. **Quick Search (< 30 s)** — Keyword or "I'm feeling lucky" search; immediate results with hiring-status badges.
2. **Advanced Discovery (5 min)** — Multi-faceted filtering by research area, location, lab size, skills; compatibility scoring; side-by-side comparison.
3. **Deep Dive (15 min per lab)** — Full lab profile: team, projects, publications, deadlines, application instructions, compatibility breakdown.
4. **Strategic Planning (ongoing)** — Saved labs by priority, application timeline, deadline reminders, skill-development tips.

## Success Metrics

### Search Quality

| Metric | Target |
|--------|--------|
| Search P95 latency | < 2 s |
| Top-3 click-through rate | > 25% |
| User satisfaction with matches | > 4/5 |
| False positive rate (non-hiring shown as hiring) | < 5% |

### Outcome Impact

| Metric | Target (Year 1) |
|--------|-----------------|
| Application success-rate improvement | > 50% over baseline |
| Time saved per student | 15+ hours |
| Platform-driven successful matches | 500+ |

### Business

| Metric | Target (Month 12) |
|--------|-------------------|
| Monthly active users | 10,000+ |
| Labs indexed | 50,000+ |
| 30-day retention | > 40% |

## Implementation Phases

| Phase | Timeframe | Focus | Key Deliverable |
|-------|-----------|-------|----------------|
| 1 — MVP | Months 1–3 | Manual data, basic search | 1,000 labs, keyword search, simple profiles |
| 2 — Automated Collection | Months 4–6 | Web scraping, API integrations | 10,000 labs, automated hiring-intent signals |
| 3 — Intelligent Matching | Months 7–9 | ML models, personalization | Compatibility scoring, recommendations, A/B testing |
| 4 — Comprehensive Platform | Months 10–12 | Real-time updates, full ecosystem | 50,000+ labs, continuous learning, community corrections |

## Competitive Advantages

1. **Data advantage** — Real-time hiring-intent detection vs. static/annual data from competitors.
2. **Technology advantage** — ML-powered matching and success prediction vs. keyword search.
3. **UX advantage** — Actionable insights and integrated workflow vs. information-only directories.
4. **Network effects** — More users produce more feedback, improving data quality and match accuracy, which attracts more users.

## Why This Will Win

The search engine solves a real, painful problem: students waste 20+ hours researching labs that may not even be hiring, while professors struggle to find qualified applicants. By detecting hiring intent in real time and matching it with student capabilities, TorchMail creates **10x value** for both sides. This is the foundation on which every other TorchMail feature — email generation, application tracking, community — is built.

---

*Document Version: 2.0*
*Last Updated: March 19, 2026*
*Next Review: April 19, 2026*
*Owner: Search Engine Product Lead*
