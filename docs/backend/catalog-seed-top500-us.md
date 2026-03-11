# Catalog Seed Contract (Top-N US by Market Cap, Starter Plan)

Last updated: 2026-03-01  
Status: Implemented contract for maintenance seed path.

## 1) Scope

- Maintenance domain seeds `stock_catalog` with a deterministic top-N US stock universe.
- This replaces direct S&P500 constituent ingestion when that endpoint is unavailable in Starter plan.
- Admin-only trigger path:
  - `POST /api/v1/admin/maintenance/catalog/seed/top-us-market-cap`
  - `GET /api/v1/admin/maintenance/catalog/seed-runs/{run_id}`
  - `GET /api/v1/admin/maintenance/catalog/seed-runs`

## 2) Endpoint Contracts (Hybrid Strategy)

The provider adapter attempts stable endpoints first and falls back to v3 when needed.

### Directory baseline

- Stable candidate: `/stable/stock-list`
- v3 fallback: `/api/v3/stock/list`
- Purpose: canonical symbol inventory and baseline identity filtering.

### Universe selection

- Stable candidate: `/stable/company-screener`
- v3 fallback: `/api/v3/stock-screener`
- Parameters:
  - `country=US`
  - `isActivelyTrading=true`
  - `isEtf=false`
  - `isFund=false`
  - `marketCapMoreThan={MAINTENANCE_SEED_MIN_MARKET_CAP}`
  - `limit=5000`
- Purpose: market-cap source for deterministic top-N selection (and seed enrichment fields).

## 3) Deterministic Selection Spec

- Symbol normalization: `trim + uppercase`.
- Candidate universe: intersection of directory candidates and screener symbols with positive market cap.
- Ranking:
  1. `market_cap DESC`
  2. `symbol ASC` (tie-break)
- Seed target cardinality: exactly `N` (`MAINTENANCE_SEED_TARGET_COUNT`, default `100`).

## 4) Persistence Contracts

### `catalog_seed_runs`

- Tracks:
  - run scope/status
  - endpoint strategy and endpoint usage
  - selected/inserted/updated counters
  - error code/message and timestamps

### `stock_catalog`

- Resolver fields:
  - `symbol`, `name_display`, `name_normalized`, `is_active`
- Ranking/context fields:
  - `market_cap`, `sector`, `industry`, `country`, exchange fields
  - `selection_rank`, `selection_method`
- Provenance:
  - `source`, `source_updated_at`, `seed_run_id`

## 5) Quality Gates

- Seed fails if selected symbol count is not `N` (`MAINTENANCE_SEED_TARGET_COUNT`).
- Seed fails on provider-level hard errors (e.g. unauthorized, plan-restricted, rate-limited, endpoint/schema failure).

## 6) Resolve Query Readiness Criteria

`resolve_query` implementation can start when:

1. At least one seed run has `status=succeeded`.
2. `stock_catalog` has at least `MAINTENANCE_SEED_TARGET_COUNT` active rows with unique `symbol`.
3. Every row has non-empty `name_normalized`.
4. `selection_rank` is populated and reproducible from source data.
5. Endpoint usage diagnostics are available in `catalog_seed_runs` for operational troubleshooting.
