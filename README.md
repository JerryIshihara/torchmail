# TorchMail - Research Assistant SaaS Platform

## Overview
TorchMail is a SaaS platform that helps students automate the process of finding research assistant positions. We start with AI-powered cold email tools and expand into a comprehensive matching platform connecting students with research opportunities.

## Problem Statement
Students struggle to:
- Identify relevant research opportunities
- Craft personalized cold emails to professors
- Track multiple applications efficiently
- Match their skills with appropriate research projects

## Solution
TorchMail provides:
1. **🎯 Research Lab Search Engine** (Core Competitive Advantage): Intelligent platform that identifies professors actively seeking research assistants using real-time data analysis and ML-powered hiring intent detection
2. **📧 AI-Powered Email Generator**: Personalized cold emails tailored to specific professors and research areas
3. **📊 Professor Database**: Comprehensive directory of researchers with dynamic hiring status tracking
4. **🤝 Smart Matching**: Multi-dimensional compatibility scoring (skills, research, timing, culture)
5. **📋 Application Tracker**: Centralized dashboard to manage all applications with success prediction
6. **👥 Community Platform**: Resources and networking for aspiring researchers

### 🚀 Key Innovation: Hiring Intent Detection
Traditional directories show ALL professors → TorchMail shows ONLY professors who are ACTIVELY HIRING, saving students 15+ hours of manual research and increasing application success rates by 50%+.

## Target Users
- Undergraduate students seeking research experience
- Graduate students looking for RA positions
- International students navigating unfamiliar academic systems
- Professors seeking qualified research assistants

## Technology Stack (Search MVP — shipped)
- **Frontend**: React 19 + Vite 7 + Tailwind CSS 4
- **Backend**: Python FastAPI + Uvicorn
- **Database**: Supabase PostgreSQL (SQLAlchemy ORM)
- **Research data**: OpenAlex API
- **Deploy**: Vercel (frontend) + Railway (backend)

## Business Model
- **Freemium**: Basic features free, premium features subscription-based
- **Tiered Pricing**: Student, institutional, and enterprise plans
- **University Partnerships**: Bulk licensing for career centers

## Roadmap
### Phase 1 (MVP): AI Email Generator
- Personalized cold email generation
- Template library
- Basic tracking

### Phase 2: Platform Expansion
- Professor database
- Matching algorithm
- Application tracker

### Phase 3: Full Platform
- Two-sided marketplace
- Community features
- Advanced analytics

## Comprehensive Documentation
TorchMail has extensive documentation to guide development:

### Product Design (`/docs/product-design/`)
- **Epics & Milestones**: 7 major epics with 21 milestones
- **Technical Designs**: Detailed architecture for core components
- **Search Engine**: Complete requirements and technical design for the core competitive advantage
- **Implementation Roadmap**: 12-month detailed development plan
- **Architecture Diagrams**: Mermaid diagrams for system visualization

### Product Management (`/docs/product-management/`)
- **Iteration Workflow**: Standardized product development process
- **PRD Template**: Product Requirements Document template

### Development Processes (`/docs/`)
- **PR Process**: Pull Request creation, review, and merge workflows
- **Project Structure**: Detailed directory organization and development guidelines

## Getting Started

```bash
git clone https://github.com/JerryIshihara/torchmail.git
cd torchmail
cp .env.example .env        # fill in DATABASE_URL and OPENALEX_EMAIL
```

### Backend (FastAPI)

```bash
pip install -r src/search_engine/requirements.txt -r src/backend/requirements.txt
PYTHONPATH=src python -m search_engine init-db   # create tables (idempotent)
PYTHONPATH=src uvicorn src.backend.main:app --reload
# API available at http://127.0.0.1:8000
```

### Frontend (Vite + React + Tailwind)

```bash
cd src/frontend
npm install
npm run dev
# UI available at http://127.0.0.1:5173 — proxies /api/* to :8000
```

### API quick test

```bash
# Search globally — priority countries (US/GB/HK/SG) ranked first
curl "http://127.0.0.1:8000/api/search?q=machine+learning"

# Scope to specific countries
curl "http://127.0.0.1:8000/api/search?q=machine+learning&countries=US,GB"
```

### CLI (interactive search, no server needed)

```bash
PYTHONPATH=src python -m search_engine          # interactive loop
PYTHONPATH=src python -m search_engine search "CRISPR"
PYTHONPATH=src python -m search_engine stats    # DB row counts
```

## Deployment

- Production deployment guide: `docs/deployment/production-deployment.md`
- Railway backend config: `railway.json`, `src/backend/Dockerfile`
- Vercel frontend rewrite config: `src/frontend/vercel.json`
- Auto-deploy workflow: `.github/workflows/deploy.yml`

## Contributing
We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License
MIT License - see [LICENSE](LICENSE) for details.

## Contact
- GitHub: [@JerryIshihara](https://github.com/JerryIshihara)
- Project Link: [https://github.com/JerryIshihara/torchmail](https://github.com/JerryIshihara/torchmail)