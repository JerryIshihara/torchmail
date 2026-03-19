# TorchMail — Project Plan

> Single source of truth for project scope, phasing, and issue tracking.
> All issues are tracked on GitHub: [Issues](https://github.com/JerryIshihara/torchmail/issues)

---

## Current State

| Component | Status |
|-----------|--------|
| Product design docs | Done (7 epics, 21 milestones) |
| Search engine MVP | Done (Python CLI + OpenAlex + PostgreSQL) |
| DBML schema | Done (`docs/schema/`) |
| Frontend (Next.js) | Not started |
| Backend API (FastAPI) | Not started |
| AI email generator | Not started |
| Matching engine | Not started |
| Application tracker | Not started |
| Community platform | Not started |
| Monetization | Not started |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Users (Students)                      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Next.js Frontend (Vercel)                   │
│  Landing · Dashboard · Search · Email · Tracker · Forum │
└────────────────────────┬────────────────────────────────┘
                         │ REST / tRPC
┌────────────────────────▼────────────────────────────────┐
│            FastAPI Backend (Railway/Render)              │
│  Auth · Search · Email Gen · Matching · Tracker · Admin │
└───┬──────────┬──────────┬──────────┬────────────────────┘
    │          │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼────┐
│ Supa- │ │ Redis │ │OpenAI │ │OpenAlex│
│ base  │ │(Upstash)│ │ API  │ │  API   │
│ (PG)  │ │       │ │       │ │        │
└───────┘ └───────┘ └───────┘ └────────┘
```

---

## Phase Overview

| Phase | Focus | Issues | Key Deliverable |
|-------|-------|--------|-----------------|
| **1 — Foundation** | Scaffolding, email MVP, deploy, monetization | #5 #6 #7 #8 #9 #10 | Beta launch with email generator |
| **2 — Core Platform** | Professor DB web UI, matching, app tracker | #11 #12 #13 #14 | Public launch with full feature set |
| **3 — Advanced** | Deep personalization, AI matching, community, data pipelines | #15 #16 #17 #18 | 5,000 users, ML-powered matching |
| **4 — Scale** | Performance, security, business, intelligence | #19 #20 #21 #22 #23 | 10,000 users, enterprise-ready |

---

## Phase 1: Foundation

> Goal: Get a working product in front of 100 beta users.

| # | Issue | Epic | Priority | Dependencies |
|---|-------|------|----------|--------------|
| 5 | [Project scaffolding — monorepo, CI/CD, dev env](https://github.com/JerryIshihara/torchmail/issues/5) | Infra | P0 | — |
| 6 | [Authentication — Supabase Auth](https://github.com/JerryIshihara/torchmail/issues/6) | Infra | P0 | #5 |
| 7 | [AI email generator MVP — templates + OpenAI](https://github.com/JerryIshihara/torchmail/issues/7) | Epic 1.1 | P0 | #5 #6 |
| 8 | [Production deployment — Vercel + Railway](https://github.com/JerryIshihara/torchmail/issues/8) | Epic 6.1 | P0 | #5 |
| 9 | [Basic monetization — Stripe + freemium](https://github.com/JerryIshihara/torchmail/issues/9) | Epic 7.1 | P1 | #5 #6 |
| 10 | [Beta launch — 100 users, feedback](https://github.com/JerryIshihara/torchmail/issues/10) | Launch | P0 | #7 #8 #9 |

### Execution order

```
#5 Project scaffolding
 ├─► #6 Authentication   ─┐
 ├─► #8 Prod deployment   ├─► #7 Email generator MVP ─┐
 └────────────────────────┘                            │
      #9 Monetization ─────────────────────────────────┤
                                                       ▼
                                               #10 Beta launch
```

### Exit criteria
- `npm run dev` starts frontend + backend locally
- Users can sign up, generate emails, and copy/save them
- App is deployed to production URL
- Stripe payments work end-to-end
- 100 beta users onboarded

---

## Phase 2: Core Platform

> Goal: Public launch with search, matching, and application tracking.

| # | Issue | Epic | Priority | Dependencies |
|---|-------|------|----------|--------------|
| 11 | [Professor database MVP — web UI, profiles, search](https://github.com/JerryIshihara/torchmail/issues/11) | Epic 2.1 | P0 | #5 #6 |
| 12 | [Basic matching engine — profiles + scoring](https://github.com/JerryIshihara/torchmail/issues/12) | Epic 3.1 | P0 | #11 |
| 13 | [Application tracker — board, deadlines, docs](https://github.com/JerryIshihara/torchmail/issues/13) | Epic 4.1 | P1 | #5 #6 #7 |
| 14 | [Public launch — 1,000 users, marketing](https://github.com/JerryIshihara/torchmail/issues/14) | Launch | P0 | All Phase 2 |

### Execution order

```
#11 Professor DB MVP
 └─► #12 Basic matching ─┐
                          ├─► #14 Public launch
#13 Application tracker ──┘
```

### Exit criteria
- Web-based professor search with profiles and bookmarking
- Student profiles with compatibility scores and recommendations
- Kanban application tracker with reminders
- 1,000+ active users, $5K+ MRR

---

## Phase 3: Advanced Features

> Goal: Deep personalization, ML matching, community, and automated data.

| # | Issue | Epic | Priority | Dependencies |
|---|-------|------|----------|--------------|
| 15 | [Advanced personalization — paper analysis, tone, scoring](https://github.com/JerryIshihara/torchmail/issues/15) | Epic 1.2 | P1 | #7 #11 |
| 16 | [Advanced AI matching — ML models, prediction](https://github.com/JerryIshihara/torchmail/issues/16) | Epic 3.2 | P1 | #12 |
| 17 | [Community features — forums, Q&A](https://github.com/JerryIshihara/torchmail/issues/17) | Epic 5.1 | P2 | #5 #6 |
| 18 | [Automated data collection — scraping, arXiv](https://github.com/JerryIshihara/torchmail/issues/18) | Epic 2.2 | P1 | #11 |

### Exit criteria
- Email quality scoring > 4/5 average
- ML matching outperforms keyword matching by 20%+
- Community forums active with 100+ posts
- Database: 20,000+ professors from automated pipelines

---

## Phase 4: Scale & Optimize

> Goal: Enterprise readiness, 10K users, institutional adoption.

| # | Issue | Epic | Priority | Dependencies |
|---|-------|------|----------|--------------|
| 19 | [Performance & reliability — caching, auto-scaling](https://github.com/JerryIshihara/torchmail/issues/19) | Epic 6.2 | P1 | #8 |
| 20 | [Advanced business — tiered pricing, university licensing](https://github.com/JerryIshihara/torchmail/issues/20) | Epic 7.2 | P1 | #9 |
| 21 | [Real-time research intelligence — trends, grants](https://github.com/JerryIshihara/torchmail/issues/21) | Epic 2.3 | P2 | #18 |
| 22 | [Security, compliance & multi-tenancy](https://github.com/JerryIshihara/torchmail/issues/22) | Epic 6.3 | P1 | #6 #8 |
| 23 | [Learning resources & mentorship matching](https://github.com/JerryIshihara/torchmail/issues/23) | Epic 5.2 | P2 | #17 |

### Exit criteria
- p95 API latency < 200ms
- Platform supports 10,000 concurrent users
- University licensing available
- FERPA/GDPR compliance documented
- 50,000+ professors in database

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Next.js 14 + TypeScript + Tailwind CSS | SSR, fast iteration, great DX |
| **Backend** | Python FastAPI | Async, type-safe, ML ecosystem |
| **Database** | Supabase (PostgreSQL) | Free tier, auth, storage, realtime |
| **Cache** | Upstash Redis | Serverless, pay-per-request |
| **AI** | OpenAI GPT-4 | Email generation, paper analysis |
| **Research data** | OpenAlex API | Free, comprehensive, no key needed |
| **Payments** | Stripe | Industry standard, great API |
| **Deployment** | Vercel (frontend) + Railway (backend) | Fast deploys, free tiers |
| **Monitoring** | Sentry + Axiom | Error tracking + logging |
| **Email** | Resend | Developer-friendly transactional email |

---

## GitHub Project Board Setup

Since GitHub Projects require owner permissions, follow these steps to create the board:

### 1. Create the project

1. Go to https://github.com/JerryIshihara/torchmail
2. Click **Projects** tab → **New project**
3. Choose **Board** template
4. Name it **TorchMail Development Roadmap**

### 2. Configure columns

Create these columns (status field):

| Column | Description |
|--------|-------------|
| **Backlog** | Not yet scheduled |
| **Phase 1** | Foundation — current focus |
| **Phase 2** | Core Platform — next up |
| **Phase 3** | Advanced Features |
| **Phase 4** | Scale & Optimize |
| **In Progress** | Currently being worked on |
| **Done** | Completed |

### 3. Add issues to the project

1. In the project board, click **+ Add item**
2. Search for each issue by number (#4 through #23)
3. Drag issues into the appropriate phase column

### 4. Recommended custom fields

| Field | Type | Values |
|-------|------|--------|
| **Priority** | Single select | P0-Critical, P1-High, P2-Medium, P3-Low |
| **Epic** | Single select | Email, Database, Matching, Application, Community, Infra, Monetization |
| **Phase** | Single select | Phase 1, Phase 2, Phase 3, Phase 4 |

### 5. Create views

- **Board view** (default): Group by Status
- **Table view**: Sort by Priority, filter by Phase
- **Roadmap view**: Timeline by Phase (if using GitHub Projects timeline)

### 6. Recommended labels

Run these commands (requires repo admin access):

```bash
gh label create "phase:1-foundation"   --color "0E8A16" --description "Phase 1: Foundation"
gh label create "phase:2-core"         --color "1D76DB" --description "Phase 2: Core Platform"
gh label create "phase:3-advanced"     --color "D93F0B" --description "Phase 3: Advanced Features"
gh label create "phase:4-scale"        --color "5319E7" --description "Phase 4: Scale & Optimize"
gh label create "epic:1-email"         --color "FBCA04" --description "Epic 1: AI Email Generation"
gh label create "epic:2-database"      --color "B60205" --description "Epic 2: Professor Database"
gh label create "epic:3-matching"      --color "006B75" --description "Epic 3: Smart Matching"
gh label create "epic:4-application"   --color "D4C5F9" --description "Epic 4: Application Management"
gh label create "epic:5-community"     --color "F9D0C4" --description "Epic 5: Community & Learning"
gh label create "epic:6-infra"         --color "C2E0C6" --description "Epic 6: Infrastructure"
gh label create "epic:7-monetization"  --color "FEF2C0" --description "Epic 7: Monetization"
gh label create "priority:p0-critical" --color "B60205" --description "Must have for launch"
gh label create "priority:p1-high"     --color "D93F0B" --description "Important"
gh label create "priority:p2-medium"   --color "FBCA04" --description "Nice to have"
```

---

## Issue Index

| # | Title | Phase | Epic | Priority |
|---|-------|-------|------|----------|
| 4 | Search Engine MVP (Complete) | Pre-1 | — | Done |
| 5 | Project scaffolding — monorepo, CI/CD, dev env | 1 | Infra | P0 |
| 6 | Authentication — Supabase Auth | 1 | Infra | P0 |
| 7 | AI email generator MVP — templates + OpenAI | 1 | Epic 1.1 | P0 |
| 8 | Production deployment — Vercel + Railway | 1 | Epic 6.1 | P0 |
| 9 | Basic monetization — Stripe + freemium | 1 | Epic 7.1 | P1 |
| 10 | Beta launch — 100 users, feedback | 1 | Launch | P0 |
| 11 | Professor database MVP — web UI, profiles, search | 2 | Epic 2.1 | P0 |
| 12 | Basic matching engine — profiles + scoring | 2 | Epic 3.1 | P0 |
| 13 | Application tracker — board, deadlines, docs | 2 | Epic 4.1 | P1 |
| 14 | Public launch — 1,000 users, marketing | 2 | Launch | P0 |
| 15 | Advanced personalization — paper analysis, tone | 3 | Epic 1.2 | P1 |
| 16 | Advanced AI matching — ML models, prediction | 3 | Epic 3.2 | P1 |
| 17 | Community features — forums, Q&A | 3 | Epic 5.1 | P2 |
| 18 | Automated data collection — scraping, arXiv | 3 | Epic 2.2 | P1 |
| 19 | Performance & reliability | 4 | Epic 6.2 | P1 |
| 20 | Advanced business — tiered pricing | 4 | Epic 7.2 | P1 |
| 21 | Real-time research intelligence | 4 | Epic 2.3 | P2 |
| 22 | Security, compliance & multi-tenancy | 4 | Epic 6.3 | P1 |
| 23 | Learning resources & mentorship | 4 | Epic 5.2 | P2 |

---

## What to Build First

Start with **#5 (Project scaffolding)** — everything else depends on it. The critical path to beta launch is:

```
#5 → #6 → #7 → #10
#5 → #8 ──────► #10
#5 → #6 → #9 ─► #10
```

All three tracks (#7 email gen, #8 deployment, #9 monetization) can proceed in parallel once scaffolding and auth are done.
