# CFAI API Contract

Bridge between Next.js (frontend) and Motia backend.

## Overview

- **Frontend**: Next.js server actions and API routes. Users never call the backend directly.
- **Backend**: Motia on port 3001. Protected by `X-API-Key`. Only Next.js server-side code calls it.
- **Auth**: NextAuth (Google). Session required for analysis triggers. Backend trusts API key only.

## Backend Endpoints

All backend requests **must** include header: `X-API-Key: <BACKEND_API_KEY>`.

### 1. Trigger Stock Analysis

**Request**

```
GET /stock/search?symbol=AAPL
Headers: X-API-Key: <key>
```

**Response** `200`

```json
{
  "message": "Stock analysis request received for AAPL",
  "status": "processing",
  "traceId": "clx..."
}
```

**Next.js usage**: Server action `triggerAnalysis(ticker)` or `forceRefreshAnalysis(ticker)` calls this.

---

### 2. Analysis Status Stream (SSE)

**Request**

```
GET /analysis/:traceId/stream
Headers: X-API-Key: <key>
```

**Response**: `text/event-stream`

```
data: {"traceId":"clx...","symbol":"AAPL","status":"Gemini is analyzing the stock..."}

data: {"traceId":"clx...","symbol":"AAPL","status":"Analysis completed"}
```

**Next.js usage**: Route `/api/analysis/[traceId]/stream` proxies this to the client. Client uses `EventSource` or `useAnalysisStream` hook.

---

## Data Flow

1. User visits `/analysis/AAPL`
2. Next.js `getAnalysis(ticker)` checks PostgreSQL cache (7-day TTL)
3. If cache miss:
   - `triggerAnalysis(ticker)` → `GET /stock/search?symbol=AAPL` (with API key)
   - Backend returns `traceId`, emits event for async pipeline
   - Frontend shows loading, subscribes to `/api/analysis/[traceId]/stream`
   - SSE streams status updates until "Analysis completed"
   - Next.js revalidates, fetches fresh data from DB
4. If cache hit: render immediately

## Environment Variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `BACKEND_URL` | Web (server) | URL to reach backend (e.g. `http://backend:3001`) |
| `BACKEND_API_KEY` | Web + Backend | Shared secret for API authentication |
| `DATABASE_URL` | Web + Backend | PostgreSQL connection |
| `REDIS_URL` | Backend | Redis for state, BullMQ, FMP cache, status pub/sub |

## Shared Types

`@repo/types` defines Zod schemas used by both apps:

- `PackedAnalysisData` – full analysis result stored in DB
- `DCFResult`, `StockRating`, `StockQualitativeAnalysis`, etc.

These ensure FE and BE agree on data shapes without runtime drift.
