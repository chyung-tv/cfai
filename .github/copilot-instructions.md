# CFAI - AI-Powered Stock Analysis Platform

## 1. Project Architecture & Context

**Monorepo Structure**: Turborepo with two independent services sharing a database:

- `apps/backend`: **Motia** event-driven analysis engine (port 3001)
- `apps/web`: **Next.js 15** frontend with NextAuth (port 3000)
- `packages/db`: Shared Prisma schema and client
- `packages/types`: Shared Zod schemas exported by both services

**Service Boundaries**: Backend and web communicate via HTTP APIs, real-time streams, and shared database access. Never import backend code into web or vice versa—use shared packages (`@repo/types`, `@repo/db`).

## 2. Backend Development (Motia Framework)

**Core Primitive**: The **Step** (`*.step.ts`). Each step exports `config` (type, schemas, emits) and `handler` (async function).

**Step Types**:

- **API Steps**: HTTP endpoints (`stock-analysis-api.step.ts` → emits event → returns immediately)
- **Event Steps**: Background processing (`dcf.step.ts`, `judgement.step.ts` → heavy AI/compute work)
- **Cron Steps**: Scheduled tasks
- **Stream Steps**: Real-time WebSocket updates (`.stream.ts`)

**Event-Driven Flow Pattern**:

```typescript
// API Step emits event immediately
await emit({ topic: "process-stock-analysis", data: { symbol } });

// Event step subscribes to topic
subscribes: ["process-stock-analysis"];
```

**State Management** (Critical):

- **Write**: `await state.set("key", traceId, data)`
- **Read**: **ALWAYS** use `getValidatedState("key", schema, state, traceId, logger)` from `steps/lib/statehooks.ts`
- **Why**: Validates type safety and runtime correctness between decoupled steps

**Real-Time Streams**:

- Update clients via `streams["stock-analysis-stream"].set("analysis", traceId, { status: "..." })`
- Clients auto-receive updates via WebSocket (see `.github/motia-stream.md`)

**Type Generation** (Non-Negotiable):

- Run `npx motia generate-types` in `apps/backend` after ANY config change
- Auto-generates `types.d.ts` with type-safe `Handlers` interface
- Every step MUST export its Zod schema to `packages/types`

## 3. Frontend Development (Next.js 15)

**Component Architecture** (Four Analysis Pillars):

1. **Business Quality**: `BusinessQualityCard` → Moat, Tier, Market Structure
2. **Valuation Reality**: `FeasibilityGauge` → Price vs. Growth Feasibility (5 scenarios)
3. **Action**: `AllocationCard` → Buy/Hold/Sell, Portfolio Role, Risk
4. **Sensitivity**: `SensitivityTable` → DCF matrix (discount rate × terminal growth)

**Data Flow**:

- Current: Mock data in `(marketing)/page.tsx`
- Future: Connect to `stock-analysis-stream` for real-time updates via `@motiadev/stream-client-react`

**Styling**: Tailwind CSS with `lucide-react` icons

## 4. AI & Financial Logic

**AI Provider**: Vercel AI SDK (`@ai-sdk/google`) with Gemini models (`gemini-2.0-flash-exp`)

**Pattern**: Always use `generateObject` with strict Zod schemas:

```typescript
const result = await generateObject({
  model: google("gemini-2.0-flash-exp"),
  schema: growthJudgementSchema,
  prompt: "...",
});
```

**Key AI Functions** (in `apps/backend/steps/lib/ai-functions/`):

- `parseThesis.ts`: Extract Porter's 5 Forces, growth drivers from research
- `judgement.ts`: AI predicts realistic growth vs. market-implied growth
- `rating.ts`: Comprehensive qualitative rating (Tier, Moat, Action)

**Financial Models**:

- **Reverse DCF**: Solves for implied growth rate given current price
- **Forward DCF**: Calculates intrinsic value from AI's growth projection
- **Sensitivity Analysis**: 5×5 matrix (discount rate ±1% × terminal growth ±0.5%)

## 5. Database Schema (Prisma)

**Key Models**:

- `User`: NextAuth user with `hasAccess` boolean (closed beta flag)
- `AnalysisResult`: Cached stock analysis (1 per ticker per TTL), stores JSON blobs (`thesis`, `dcf`, `rating`)
- `UserQuery`: Tracks user requests with `traceId` for real-time updates

**Access Pattern**: Backend writes via `@repo/db`, frontend reads via server actions/API routes.

## 6. Critical Workflows & Commands

```bash
# Start everything
pnpm dev                          # Root (runs both backend + web)

# Backend only
cd apps/backend
pnpm dev                          # Starts Motia Workbench at :3001
npx motia generate-types          # Regenerate types after config changes

# Database
cd packages/db
npx prisma migrate dev            # Create migration
npx prisma studio                 # Visual DB browser

# Type checking
pnpm run check-types              # Validates all workspace types
```

## 7. Critical Patterns & Conventions

**Shared Types**:

- Always export schemas from `packages/types/src/*.ts`
- Import as `import { dcfResultSchema } from "@repo/types"`
- Maintain single source of truth for types

**State Validation**:

- Never use `state.get()` directly—use `getValidatedState()` to catch schema drift
- Example: `const dcf = await getValidatedState("dcf", dcfResultSchema, state, traceId, logger)`

**Event Chaining**:

- List all emits in step config: `emits: ["finish-dcf"]`
- Downstream steps subscribe: `subscribes: ["finish-dcf"]`
- Check `.cursor/rules/motia/event-steps.mdc` for patterns

**Real-Time Updates**:

- Stream status updates at each step boundary for UX feedback
- Pattern: `streams["stock-analysis-stream"].set("analysis", traceId, { status: "Calculating DCF..." })`

## 8. Deployment Architecture

**⚠️ Critical**: Frontend and backend **MUST** be deployed separately.

**Why Separate Deployments:**

- Motia requires persistent WebSocket connections (streams) and long-running BullMQ workers
- Vercel serverless functions timeout after 60-300s (incompatible with Motia)
- Backend needs Redis for state management and job queuing

**Recommended Setup:**

```
Frontend (apps/web)    → Vercel (Next.js serverless)
Backend (apps/backend) → Motia Cloud (managed Motia hosting)
Database               → Vercel Postgres (shared)
```

**Alternative (Self-Hosted):**

```
Frontend (apps/web)    → Vercel
Backend (apps/backend) → Railway/Render (Docker + Redis)
Database               → Vercel Postgres
```

**Environment Variables:**

- Vercel manages env vars via dashboard UI (no `.env` files in deployment)
- See `.env.example` for all required variables
- `turbo.json` configured with `env` arrays for proper cache invalidation
- Different `NEXTAUTH_SECRET` for staging vs production

**Detailed Guide**: See `.github/DEPLOYMENT.md` for step-by-step deployment instructions.

## 9. Common Pitfalls

- **Missing Types**: If you see TypeScript errors in handlers, run `npx motia generate-types`
- **Direct State Access**: Using `state.get()` without validation causes silent type mismatches
- **Heavy API Logic**: API steps should emit events, not perform compute (use Event steps)
- **Schema Drift**: Always re-export schemas from `packages/types` to keep frontend/backend in sync
- **Overlapping Concerns**: Keep "Quality" (business strength) separate from "Valuation" (price vs. growth math)
- **Deploying Backend to Vercel**: Will fail silently or timeout—use Docker/Railway instead
