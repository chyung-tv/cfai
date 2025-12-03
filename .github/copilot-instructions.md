# CFAI - AI-Powered Stock Analysis Platform

## Project Architecture

This is a **Turborepo monorepo** with two distinct backend systems working together:

- **`apps/backend`** - Motia-based event-driven stock analysis engine (port 3001)
- **`apps/web`** - Next.js 16 frontend with NextAuth for user management
- **`packages/db`** - Shared Prisma database layer used by both apps

### Critical: Two Separate Backend Systems

The backend and web apps are **independent services** that communicate via HTTP:

- Backend exposes Motia API endpoints (`/stock/search`, `/api/history`)
- Web app consumes these endpoints and handles auth/UI
- Both share the same Postgres database via `@repo/db` package

## Motia Framework Patterns

### Event-Driven Stock Analysis Flow

The stock analysis workflow is a **multi-step event chain** managed by Motia:

```
API Step (stock-analysis-api.step.ts)
  ↓ emits "process-stock-analysis"
Event Step (qualitative-analysis.step.ts)
  ↓ emits "finish-qualitative-analysis"
Event Step (projection-judge.step.ts)
  ↓ emits "finish-projection-judge"
Event Step (dcf.step.ts)
  ↓ emits "finish-dcf"
Event Step (rating.step.ts)
  ↓ emits "finish-stock-rating"
Event Step (return-db.step.ts) - Saves to DB & writes to stream
```

**Key Principle**: Each step emits events to trigger the next step. Steps communicate via:

1. **Events** - Lightweight triggers with minimal data (`{symbol: string}`)
2. **State** - Persistent data storage using `state.set()` / `state.get()` with `traceId` as key
3. **Streams** - Real-time updates to frontend (`stock-analysis-stream`)

### State Management Pattern

All steps follow this pattern for data sharing:

```typescript
// Writer step: Save validated data to state
await state.set("dcf", traceId, dcfResult);

// Reader step: Retrieve and validate using statehooks
const dcfData = await getValidatedState(
  "dcf",
  dcfResultSchema,
  state,
  traceId,
  logger
);
```

**Always use `getValidatedState()` from `steps/lib/statehooks.ts`** - it enforces type safety and provides clear error messages when data is missing or malformed.

### Motia Step Naming Convention

Files **must** follow this pattern:

- TypeScript: `my-step.step.ts` (kebab-case + `.step.ts` suffix)
- Each step exports `config` (type, routes, schemas, emits) and `handler` (async function)

See `apps/backend/AGENTS.md` for comprehensive Motia patterns.

## Database Strategy

### 7-Day Cache Pattern

`stock-analysis-api.step.ts` implements a **cache-first** approach:

```typescript
// 1. Check DB for analysis < 7 days old
const cachedAnalysis = await prisma.analysis.findFirst({
  where: { symbol, createdAt: { gte: sevenDaysAgo } },
});

// 2a. Cache HIT: Write to stream immediately, skip AI workflow
if (cachedAnalysis) {
  await streams["stock-analysis-stream"].set("analysis", traceId, {
    status: "Completed (Cached)",
    data: cachedAnalysis.data,
  });
  return { status: "completed" };
}

// 2b. Cache MISS: Emit event to start AI analysis
await emit({ topic: "process-stock-analysis", data: { symbol } });
```

**Always check the cache before starting expensive AI operations.**

### Prisma Client Access

Import from the **shared package**: `import prisma from "@repo/db"` (backend) or `import { prisma } from "../../lib/db"` (if using a local wrapper).

## Workspace Commands

```bash
# Development (runs all apps in parallel)
pnpm dev                    # Starts backend:3001 + web (Next.js)

# Backend-specific
cd apps/backend
pnpm dev                    # Start Motia server + Workbench (port 3001)
npx motia generate-types    # Regenerate TypeScript types after config changes

# Database
cd packages/db
npx prisma migrate dev      # Create & apply migrations
npx prisma studio           # View database in browser

# Build everything
pnpm build                  # Turborepo builds all packages in dependency order
```

## Key Development Workflows

### Adding a New Analysis Step

1. Create `apps/backend/steps/stock-analysis/new-step.step.ts`
2. Define `config` with `subscribes: ["previous-event"]` and `emits: ["next-event"]`
3. Use `state.get()` to retrieve previous step's data, validate with Zod
4. Process data, save result with `state.set()`
5. Update stream status: `streams["stock-analysis-stream"].set(...)`
6. Run `npx motia generate-types` to regenerate type definitions

### Modifying Prisma Schema

1. Edit `packages/db/prisma/schema.prisma`
2. Run `npx prisma migrate dev --name description_of_change`
3. Prisma Client auto-regenerates - no manual codegen needed
4. Import types: `import { Analysis } from "@repo/db"`

## Project-Specific Conventions

### Type Safety with Zod

Every Motia step exports Zod schemas for validation:

```typescript
// Define and export schema
export const dcfResultSchema = z.object({
  intrinsicValuePerShare: z.number(),
  // ... other fields
});

export type DCFResult = z.infer<typeof dcfResultSchema>;
```

**Always export schemas** - they're reused by downstream steps for validation.

### Real-Time Streaming Pattern

The `stock-analysis-stream` provides live updates to the frontend:

```typescript
// Update stream at each workflow stage
await streams["stock-analysis-stream"].set("analysis", traceId, {
  id: traceId,
  symbol,
  status: "Human-readable status message",
  data: packedData, // Optional: only set when complete
});
```

Frontend connects to this stream to show progress (e.g., "Calculating DCF from verified projections...").

### Error Handling

Motia steps should **throw errors** for validation failures - the framework handles logging and retries automatically. Use Zod's `.parse()` (throws) rather than `.safeParse()` in step handlers.

## Integration Points

- **NextAuth** - Authentication in `apps/web/src/app/api/auth/[nextauth]`
- **Motia Workbench** - Visual workflow designer at `http://localhost:3001` during dev
- **BullMQ** - Event queue adapter configured in `motia.config.ts`
- **Shared Types** - `@repo/db` exports Prisma types, `@repo/ui` for shared React components
- **Vercel AI SDK** - AI provider integration using `@ai-sdk/google` for both frontend and backend

### AI Integration with Vercel AI SDK

Both apps use **Vercel AI SDK** for AI operations:

```typescript
// Backend (Motia steps): Use generateText/generateObject from ai package
import { generateObject } from "ai";
import { google } from "@ai-sdk/google";

const result = await generateObject({
  model: google("gemini-2.0-flash-exp"),
  schema: yourZodSchema,
  // ...
});
```

**Environment Variables**: AI API keys are managed in `.env` files (not documented here).

## Frontend Development Workflow

The Next.js frontend is **under active development**. Expect:

- Some pages may be empty or contain placeholders
- Component structure is iterative - backend/logic comes first, UI polish follows
- **Development Pattern**: Backend developer provides data/functions to components, AI assists with UI implementation
- Missing pages/components are normal during development phase

When working on frontend components, focus on functionality first, styling second.

## Testing

### Current Testing Approach

Testing infrastructure is being established. Guidelines:

- **Backend (Motia)**: Test individual step handlers by mocking `state`, `emit`, `logger` objects
- **Database**: Use test database or in-memory SQLite for Prisma tests
- **Frontend**: Consider React Testing Library for component tests
- **Integration**: Test event chains by verifying state transitions across steps

**Note**: Testing patterns are evolving. Prioritize critical paths (API endpoints, event chains) over comprehensive coverage initially.

## Common Pitfalls

- **Don't use API steps for background work** - Use Event steps for any processing > 1 second
- **Always run `generate-types` after changing step configs** - TypeScript won't know about new handlers otherwise
- **Never bypass `getValidatedState()`** - Direct `state.get()` loses type safety and error context
- **Database import mismatch** - Backend uses `@repo/db`, web may have local wrapper in `lib/db`
