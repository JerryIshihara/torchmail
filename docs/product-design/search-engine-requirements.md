# Research Lab/PI Search Engine — Requirements Specification

## 1. Overview

The Research Lab/PI Search Engine is the **core competitive advantage** of TorchMail. It helps students find professors and research labs that are actively seeking research assistants, going beyond static directories to provide dynamic, actionable intelligence.

### Critical Success Factors

| Factor | Target |
|--------|--------|
| **Accuracy** | > 90% precision in identifying labs actively seeking RAs |
| **Freshness** | Hiring-intent data updated within 7 days |
| **Relevance** | Results match the student's skills, interests, and timeline |
| **Actionability** | Every result includes clear next steps |
| **Coverage** | > 80% of research-active professors at target universities |

---

## 2. Problem Statement

### Student Pain Points

1. **Information Asymmetry** — Students cannot tell which labs are hiring.
2. **Static Directories** — Existing databases list all professors, not those seeking RAs.
3. **Timing Mismatch** — Applications arrive when labs are not actively hiring.
4. **Fit Uncertainty** — Hard to assess whether skills match lab needs.
5. **Process Inefficiency** — Manual research takes 20+ hours per student.

### Professor / Lab Pain Points

1. **Visibility Gap** — Difficult to reach qualified candidates outside their own network.
2. **Screening Overhead** — 100+ applications for 1–2 positions.
3. **Timing Issues** — Hiring needs fluctuate with grant cycles and graduation timelines.
4. **Skill Matching** — Difficult to find students with specific technical skills.

---

## 3. Functional Requirements

### FR-1: Data Collection & Enrichment

| ID | Requirement | Priority |
|----|------------|----------|
| FR-1.1 | **Hiring-intent detection** — Monitor lab websites for "positions available" / "join our lab" pages; track grant announcements; analyze publication acknowledgments for new team members; monitor social media for hiring posts. | P0 |
| FR-1.2 | **Lab profile enrichment** — Automatically populate research focus, current lab size, recent publications (last 2 years), active grants, mentorship-style indicators, and application preferences. | P0 |
| FR-1.3 | **Temporal intelligence** — Model academic hiring cycles by discipline, grant-award timelines, graduation schedules, seasonal patterns, and provide projected "likely to hire soon" estimates. | P1 |

### FR-2: Search & Discovery

| ID | Requirement | Priority |
|----|------------|----------|
| FR-2.1 | **Multi-dimensional search** — Support queries by research area / keywords, university / department, lab size, funding availability, application deadline, and skill requirements. | P0 |
| FR-2.2 | **Intelligent filtering** — Provide faceted filters: "Actively hiring", "Expected to hire soon", "Good fit for beginners", "International-student friendly", "Remote / hybrid". | P0 |
| FR-2.3 | **Relevance ranking** — Rank results by a composite score combining hiring-intent score (0–100), skill-match percentage, research alignment, timeline compatibility, and data freshness. | P0 |

### FR-3: Matching & Recommendations

| ID | Requirement | Priority |
|----|------------|----------|
| FR-3.1 | **Student profile analysis** — Capture academic background, skills, research experience, career goals, availability, geographic preferences, and funding needs. | P0 |
| FR-3.2 | **Compatibility scoring** — Compute a weighted composite: Technical Fit (40%), Research Fit (30%), Timing Fit (20%), Cultural Fit (10%). | P1 |
| FR-3.3 | **Personalized recommendations** — Surface categorized suggestions: "Best Match" (top 5), "Good Alternatives" (5), "Stretch Opportunities" (5), "Safety Options" (5). Dynamically re-rank as the student's application history grows. | P1 |

### FR-4: Action Intelligence

| ID | Requirement | Priority |
|----|------------|----------|
| FR-4.1 | **Application readiness assessment** — Score profile completeness, identify missing skills, flag incomplete documents, suggest timeline optimizations. | P1 |
| FR-4.2 | **Strategic application planning** — Recommend optimal application timing, portfolio-gap improvements, networking opportunities, and follow-up strategies. | P2 |
| FR-4.3 | **Success prediction** — Estimate interview-invitation probability, expected response time, competitive-landscape analysis, and per-application risk. | P2 |

---

## 4. Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement | Target |
|----|------------|--------|
| NFR-1.1 | Search response time (P95) | < 2 s |
| NFR-1.2 | Filter update response | < 500 ms |
| NFR-1.3 | Lab detail page load | < 1 s |
| NFR-1.4 | Recommendation generation | < 3 s |
| NFR-1.5 | Hiring-intent signals freshness | Updated daily |
| NFR-1.6 | Lab profiles freshness | Updated weekly |
| NFR-1.7 | Concurrent users supported | 10,000 |
| NFR-1.8 | Search throughput | 100+ req/s |
| NFR-1.9 | Lab profile capacity | 100,000+ |

### NFR-2: Accuracy & Quality

| ID | Requirement | Target |
|----|------------|--------|
| NFR-2.1 | Professor information accuracy | > 95% |
| NFR-2.2 | Hiring-status accuracy | > 90% |
| NFR-2.3 | Research-focus accuracy | > 85% |
| NFR-2.4 | False positive rate (non-hiring shown as hiring) | < 5% |
| NFR-2.5 | False negative rate (hiring labs missed) | < 10% |
| NFR-2.6 | Recommendation relevance (user-reported satisfaction) | > 80% |

### NFR-3: Coverage (Year 1)

| Segment | Target |
|---------|--------|
| Top 100 US R1 research universities | 100% |
| STEM departments | > 90% |
| Humanities / social sciences | > 70% |
| Top 100 global universities (international) | > 50% |

### NFR-4: Usability

- Zero-training interface; 3 clicks maximum to reach relevant labs.
- Visual hiring-status badges (urgent / active / passive).
- Mobile-responsive layout.
- Every lab result includes a clear "next step" call-to-action.
- Deadline tracking and reminder notifications.

### NFR-5: Reliability & Security

| ID | Requirement | Target |
|----|------------|--------|
| NFR-5.1 | Service uptime | 99.9% |
| NFR-5.2 | Planned maintenance downtime | < 1 h/month |
| NFR-5.3 | Disaster recovery RTO | 4 hours |
| NFR-5.4 | Encryption | At rest (AES-256) and in transit (TLS 1.3) |
| NFR-5.5 | Compliance | GDPR, CCPA, FERPA |
| NFR-5.6 | Security audits | Annual third-party pentest |

### NFR-6: Ethical Considerations

- Bias detection and mitigation in matching algorithms.
- Transparent ranking factors (users can see why a lab is ranked where it is).
- User control over data usage (opt-in to data sharing, ability to delete account and data).
- Equal access regardless of background, university prestige, or demographic characteristics.

---

## 5. Data Sources & Integration

### Primary Sources

| ID | Source | Data Provided | Update Frequency |
|----|--------|--------------|-----------------|
| DS-1 | University / lab websites | Faculty directories, "join us" pages, news | Daily crawl |
| DS-2 | Research databases (arXiv, PubMed, Semantic Scholar) | Publications, citations, co-authors | Weekly API poll |
| DS-3 | Funding databases (NSF, NIH) | Grant awards, amounts, timelines | Weekly API poll |
| DS-4 | Social / professional networks (X, LinkedIn, ResearchGate) | Hiring announcements, lab updates | Daily (rate-limited) |

### Collection Principles

- **Respectful crawling**: Obey `robots.txt`, apply polite delays (≥ 2 s between requests to the same host), identify the bot via `User-Agent`.
- **API-first**: Prefer structured APIs (Semantic Scholar, CrossRef, NSF Awards API) over scraping when available.
- **Manual curation**: Expert-verified data for the initial seed set and high-value labs; community-submitted corrections with moderation.
- **JavaScript rendering**: Use headless browser (Playwright) for SPAs; fall back to static HTML parsing otherwise.

---

## 6. User Experience Requirements

### Search Interface

- Simple keyword search box with autocomplete.
- "I'm feeling lucky" quick-match button.
- Saved searches with email/push alerts when new matching labs appear.
- Search history for logged-in users.

### Results Display

- Card-based layout showing lab name, professor, university, research areas, hiring badge, and compatibility score.
- Expandable detail panel or dedicated profile page.
- Quick-action buttons: Save, Email, Compare.

### Lab Profile Pages

- Overview: lab photo/logo, description, key stats (size, funding, publication count).
- Hiring section: current openings, deadlines, required skills, application instructions.
- Research section: active projects, recent publications, grant awards.
- Compatibility analysis (for logged-in students): skill match, research alignment, preparation tips.

### Dashboard & Management

- Saved labs organized by user-defined priority.
- Side-by-side lab comparison (up to 3).
- Application timeline visualization.
- Deadline reminders and status tracking.

---

## 7. Success Metrics & KPIs

### User Engagement

| Metric | Target (Month 6) |
|--------|------------------|
| Monthly active users (MAU) | 1,000+ |
| Searches per user per session | > 5 |
| Labs saved per user (cumulative) | > 10 |
| 30-day retention | > 40% |

### Search Quality

| Metric | Target |
|--------|--------|
| Click-through rate (top-3 results) | > 25% |
| Search abandonment rate | < 20% |
| Time to first relevant click | < 30 s |
| User-reported match satisfaction | > 4/5 |

### Outcome Impact

| Metric | Target (Year 1) |
|--------|-----------------|
| Application success-rate improvement over baseline | > 50% |
| Estimated time saved per student | 15+ hours |
| Platform-driven successful matches | 500+ |

---

## 8. Implementation Phases

### Phase 1 — MVP (Months 1–3)

**Focus**: Basic search with manually curated data.

- Static database of ~1,000 high-value labs (top CS and STEM departments).
- Manual hiring-status tagging by the team.
- Keyword search + basic filters (university, department, hiring status).
- Simple lab profile pages.
- **Exit criteria**: 100 beta users, search P95 < 2 s, user satisfaction > 4/5.

### Phase 2 — Automated Collection (Months 4–6)

**Focus**: Scale data through web scraping and API integrations.

- Automated crawling of lab websites for hiring signals.
- Integration with Semantic Scholar and NSF awards APIs.
- Expanded to ~10,000 labs.
- Basic compatibility scoring (skill overlap + research alignment).
- **Exit criteria**: > 85% hiring-status accuracy on a 200-lab audit, 1,000 MAU.

### Phase 3 — Intelligent Matching (Months 7–9)

**Focus**: ML-powered ranking and personalization.

- Hiring-intent ML classifier (binary + confidence).
- Personalized recommendations with compatibility breakdown.
- Success-probability estimates.
- A/B testing framework for ranking experiments.
- **Exit criteria**: Hiring-intent AUC > 0.85, recommendation CTR > 25%.

### Phase 4 — Comprehensive Platform (Months 10–12)

**Focus**: Real-time data, advanced analytics, full ecosystem integration.

- Near-real-time data pipeline (daily refresh for all labs).
- Advanced ML models with continuous learning from user outcomes.
- Integration with application tracker and email generator.
- Community-contributed corrections and ratings.
- **Exit criteria**: 10,000 MAU, 50,000+ labs indexed, < 5% false-positive rate.

---

## 9. Risks & Mitigations

### Technical

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Low hiring-intent accuracy in early phases | High | High | Start with manual curation; use ML only after accumulating labeled data; allow user corrections. |
| Data staleness | Medium | High | Prioritize high-value labs for frequent crawling; show "last verified" dates to users. |
| Scaling bottlenecks | Medium | Medium | Use Elasticsearch for search (horizontally scalable); cache aggressively; load-test before each phase. |
| Algorithm bias (e.g., over-representing well-known universities) | Medium | High | Diversity factor in recommendations; fairness audits each quarter; transparent ranking explanations. |

### Business

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Low user adoption | Medium | High | Start with a niche (CS research at top-30 US universities); prove value before broadening. |
| Data-sourcing legal challenges | Low | High | Consult legal counsel on web-scraping; prefer public APIs; respect robots.txt; offer opt-out for professors. |
| Competitive response from incumbents | Low | Medium | Move fast on hiring-intent detection (unique differentiator); build network effects through community. |

### Operational

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Small team bandwidth | High | Medium | Automate everything possible; prioritize ruthlessly; use managed cloud services. |
| Infrastructure cost overruns | Medium | Medium | Set per-service cost budgets; use spot instances for data pipeline; monitor cloud spend weekly. |

---

*Document Version: 2.0*
*Last Updated: March 19, 2026*
*Next Review: April 19, 2026*
*Owner: Search Engine Product Lead*
