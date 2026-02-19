# CFAI - AI-Powered Portfolio Architect

CFAI is an intelligent financial platform that shifts from passive stock analysis to active portfolio architecture. It helps "Sensible Accumulators" visualize risk clusters, stress-test portfolios, and manage constraints before buying assets.

## 🏗️ Architecture

**Monorepo** (Turborepo + pnpm):

- `apps/backend`: **Motia** event-driven analysis engine (Port 3001) – Redis state, BullMQ, SSE
- `apps/web`: **Next.js 15** frontend with NextAuth (Port 3000)
- `packages/db`: Shared Prisma schema and client
- `packages/types`: Shared Zod schemas for FE/BE contract

**VPS Deployment**: Docker Compose with Postgres, Redis, Caddy. See `docs/DEPLOYMENT-VPS.md` and `docs/API-CONTRACT.md`.

## 🚀 Core Features

### 1. The Analysis Engine ("Input Layer")

Transforms raw data into decision-ready building blocks.

- **AI Risk Auto-Tagger**: Identifies systemic and thematic risks (e.g., "AI Exposure", "China Risk").
- **Moat & Quality Scorecard**: Quantifies robustness (0.0 - 5.0) based on moat width and source.
- **Role Definition**: Contextualizes assets (Compounder, Hedge, Speculative).

### 2. The Portfolio Architect ("Interaction Layer")

The core workspace for simulation and construction.

- **Ghost Simulator**: Drag-and-drop interface to test "What If" scenarios before committing.
- **Risk Cluster Engine**: Aggregates risk tags across all holdings to warn of concentration.
- **Stress Tester**: Calculates portfolio drawdown during historical events (e.g., 2022 Inflation Shock).

## 🛠️ Tech Stack

- **Frontend**: Next.js 15, Tailwind CSS, Zustand (State Management), dnd-kit (Drag & Drop), Recharts.
- **Backend**: Motia (Event-Driven Framework), TypeScript, Vercel AI SDK (Google Gemini).
- **Database**: PostgreSQL (Prisma ORM).

## 🚦 Getting Started

### Prerequisites

- Node.js 20+
- pnpm
- PostgreSQL
- Redis

### Installation

```bash
pnpm install --ignore-scripts
cp .env.example .env
# Edit .env with DATABASE_URL, REDIS_URL, BACKEND_API_KEY, etc.
```

### Development (local)

```bash
# Option 1: Docker for Postgres + Redis only
docker compose up postgres redis -d

# Backend (REDIS_URL=redis://localhost:6379, DATABASE_URL=...)
cd apps/backend && pnpm dev

# Web (BACKEND_URL=http://localhost:3001, BACKEND_API_KEY=...)
cd apps/web && pnpm dev
```

### Production (VPS)

```bash
docker compose up -d
# First run: docker compose exec web pnpm exec prisma migrate deploy --schema=../../packages/db/prisma/schema.prisma
```

## 🔄 Workflow (The "Pivot Flow")

1.  **Phase 1: Frontend First**: Validate the "Portfolio Architect" UX with mock data.
2.  **Phase 2: Backend Overhaul**: Implement `stock-risk-flow` in Motia to power the risk engine.
3.  **Phase 3: Integration**: Connect the frontend to live Motia streams and database.

## 📄 License

Private - All rights reserved.
