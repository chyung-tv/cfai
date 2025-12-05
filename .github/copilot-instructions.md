# CFAI - AI-Powered Stock Analysis Platform

## 1. Project Architecture & Context

- **Monorepo Structure**: Turborepo with two distinct services sharing a database.
  - `apps/backend`: **Motia** framework (Event-driven analysis engine). Port 3001.
  - `apps/web`: **Next.js 16** frontend (UI, Auth, Dashboard). Port 3000.
  - `packages/db`: Shared **Prisma** schema and client.
- **Service Boundaries**:
  - Backend and Web are **independent**. They communicate via HTTP APIs and shared DB access.
  - **Never** import backend code directly into the web app or vice versa. Use shared packages.

## 2. Backend Development (Motia Framework)

- **Core Primitive**: The **Step** (`*.step.ts`).
  - **API Steps**: Handle HTTP requests (e.g., `stock-analysis-api.step.ts`).
  - **Event Steps**: Handle background logic (e.g., `dcf.step.ts`, `rating.step.ts`).
  - **Cron Steps**: Handle scheduled tasks.
- **Event-Driven Flow**:
  - Steps emit events to trigger downstream steps: `await emit({ topic: "next-step", data: { symbol } })`.
  - **Pattern**: API -> Event -> Event -> ... -> DB/Stream.
- **State Management**:
  - **Write**: `await state.set("key", traceId, data)`.
  - **Read**: **ALWAYS** use `getValidatedState("key", schema, state, traceId, logger)` from `steps/lib/statehooks.ts`.
  - **Why**: Ensures type safety and runtime validation between decoupled steps.
- **Type Safety**:
  - **Crucial**: Run `npx motia generate-types` in `apps/backend` after ANY change to step config (inputs/emits).
  - **Zod**: Every step **must** export its output schema (e.g., `export const dcfResultSchema = z.object(...)`).

## 3. Frontend Development (Next.js 16)

- **Component Architecture**:
  - **Analysis Pillars**:
    1.  **Business Quality**: `BusinessQualityCard` (Moat, Tier, Structure).
    2.  **Valuation Reality**: `FeasibilityGauge` (Price vs. Growth Math).
    3.  **Action**: `AllocationCard` (Buy/Sell, Role, Risk).
    4.  **Sensitivity**: `SensitivityTable` (Valuation Matrix).
- **Data Fetching**:
  - Currently using mock data in `page.tsx`.
  - Future state: Connect to `stock-analysis-stream` for real-time updates.
- **Styling**: Tailwind CSS 4. Use `lucide-react` for icons.

## 4. AI & Financial Logic

- **AI Provider**: Vercel AI SDK (`@ai-sdk/google`) with Gemini models (e.g., `gemini-2.5-flash`).
- **Pattern**: Use `generateObject` with strict Zod schemas for all AI outputs.
- **Key Schemas**:
  - `growthJudgementSchema`: AI's independent growth prediction vs. market implied growth.
  - `ratingSchema`: Comprehensive qualitative rating (Tier, Moat, Action).
  - `dcfResultSchema`: Financial model outputs including sensitivity matrix.
- **Financial Models**:
  - **Reverse DCF**: Calculates implied growth from current price.
  - **Forward DCF**: Calculates intrinsic value from AI projections.

## 5. Critical Workflows & Commands

- **Start All**: `pnpm dev` (Root).
- **Backend Dev**: `cd apps/backend && pnpm dev` (Runs Motia Workbench at localhost:3001).
- **Type Gen**: `cd apps/backend && npx motia generate-types` (Run frequently!).
- **DB Migration**: `cd packages/db && npx prisma migrate dev`.
- **Studio**: `cd packages/db && npx prisma studio`.

## 6. Detailed Guides & Rules

- **Motia Patterns**: Refer to `.cursor/rules/motia/` for authoritative guides on API, Event, and Cron steps.
- **Architecture**: See `.cursor/architecture/` for project structure and error handling.

## 7. Common Pitfalls to Avoid

- **Missing Types**: If you see `@ts-expect-error` in backend steps, run `generate-types`.
- **Direct State Access**: Never use `state.get()` directly for complex objects; use `getValidatedState`.
- **Overlapping UI**: Keep "Quality" (Verdict) separate from "Valuation" (Gauge). A good company can be overvalued.
- **API/Event Confusion**: Don't do heavy processing in API steps. Emit an event and process in the background.
