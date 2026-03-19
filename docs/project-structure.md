# Project Structure

## Overview
This document describes the organization of the TorchMail repository.

## Directory Structure

```
torchmail/
├── src/                    # Source code
│   ├── frontend/          # React/Next.js frontend
│   ├── backend/           # Node.js/Express backend
│   └── shared/            # Shared utilities and types
├── tests/                 # Test files
├── docs/                  # Documentation
│   ├── product-management/# Product docs (PRDs, workflows)
│   ├── architecture/      # System architecture
│   ├── api/              # API documentation
│   └── deployment/       # Deployment guides
├── scripts/              # Build and utility scripts
└── config/               # Configuration files
```

## Source Code Organization

### Frontend (`src/frontend/`)
```
frontend/
├── components/           # Reusable UI components
│   ├── common/          # Button, Input, Modal, etc.
│   ├── layout/          # Header, Footer, Sidebar
│   └── features/        # Feature-specific components
├── pages/               # Next.js pages/routes
├── hooks/               # Custom React hooks
├── utils/               # Utility functions
├── styles/              # CSS/SCSS files
├── types/               # TypeScript type definitions
├── constants/           # Application constants
└── lib/                 # Third-party library integrations
```

### Backend (`src/backend/`)
```
backend/
├── src/
│   ├── controllers/     # Request handlers
│   ├── services/        # Business logic
│   ├── models/          # Database models
│   ├── routes/          # API route definitions
│   ├── middleware/      # Express middleware
│   ├── utils/           # Utility functions
│   ├── config/          # Configuration
│   └── types/           # TypeScript types
├── tests/               # Backend tests
└── scripts/             # Database migrations, etc.
```

### Shared (`src/shared/`)
```
shared/
├── types/               # Shared TypeScript types
├── constants/           # Shared constants
├── utils/               # Shared utilities
└── schemas/             # Validation schemas (Zod, etc.)
```

## Documentation Structure

### Product Management (`docs/product-management/`)
- `iteration-workflow.md` - Standardized product development process
- `prd-template.md` - Product Requirements Document template
- `roadmap.md` - Product roadmap and milestones
- `user-research/` - User interview notes and insights
- `analytics/` - Product metrics and dashboards

### Architecture (`docs/architecture/`)
- `system-overview.md` - High-level system architecture
- `database-schema.md` - Database design and relationships
- `api-design.md` - API design principles and patterns
- `security.md` - Security architecture and practices
- `scalability.md` - Scaling strategies and considerations

### API (`docs/api/`)
- `rest-api.md` - REST API documentation
- `graphql-api.md` - GraphQL API documentation (if applicable)
- `webhooks.md` - Webhook specifications
- `authentication.md` - Authentication and authorization

### Deployment (`docs/deployment/`)
- `local-development.md` - Local setup instructions
- `production-deployment.md` - Production deployment guide
- `ci-cd.md` - Continuous Integration/Deployment setup
- `monitoring.md` - Monitoring and alerting setup
- `troubleshooting.md` - Common issues and solutions

## Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `release/*` - Release preparation branches

### Commit Convention
We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Test additions/modifications
- `chore:` - Maintenance tasks

### Code Quality
- ESLint for JavaScript/TypeScript linting
- Prettier for code formatting
- Husky for git hooks
- Jest for testing
- Cypress for E2E testing

## Getting Started

1. Clone the repository
2. Run `npm install` in root directory
3. Set up environment variables (see `.env.example`)
4. Run `npm run dev` to start development servers
5. Access frontend at `http://localhost:3000`
6. Access backend API at `http://localhost:3001`

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines.