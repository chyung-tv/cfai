# CFAI Product Blueprint (Canonical)

Last validated: 2026-03-10  
Purpose: single canonical reference for product intent, UX shape, staged delivery, and acceptance.

## 1) Problem We Are Solving

Make portfolio construction the primary user experience:
- quickly assemble a portfolio from candidate stocks
- immediately understand portfolio risk/return/concentration signals
- use stock analysis as supporting evidence material, not the main product destination

## 2) Product Intent (Agreed)

- Primary mode: portfolio builder dashboard (`portfolio-home`) as v1 north-star screen.
- Analysis workflow is an intelligence engine feeding portfolio decisions.
- Existing analysis page remains an internal observation lab for debugging/inspection.
- v1 output style: evidence-first; no explicit final buy/hold/avoid verdict.
- Data freshness policy: show cached data fast with `last updated` badge and predictable refresh behavior.
- Analysis modes:
  - default `lightweight` mode
  - explicit user action required for `deep` mode
- v1 persistence: local browser save only (no account-level portfolio persistence yet).

## Canonicality Rule

- Product behavior, UX hierarchy, and rollout stages must be defined here first.
- `roadmap.md` tracks execution status only and should not restate product specs.
- `architecture.md` tracks system design only and should reference this file for product-facing behavior.
- `architecture-decisions.md` records rationale/decision records only and should not duplicate UX specs.

## 3) Core UX Shape

### Portfolio Home (Primary)
- Start empty by default.
- Left panel (`Portfolio Builder`):
  - drag/drop or add stock
  - assign default starting weight on add
  - edit/remove positions
- Portfolio summary (always visible):
  - overall risk score
  - expected return range
  - sector concentration warning

### Candidate Feed (Integrated, Right Panel)
- Candidate card list starts from seeded stock set (~50 from DB) and can accept search inserts.
- Each card shows mixed snapshot:
  - business quality cue
  - valuation cue
  - recent change cue
  - portfolio impact cue
- Each card shows freshness badge (`last updated`).
- Card actions:
  - drag/add to portfolio
  - open `more` detail

### Stock Detail (From `more`)
- Keep existing depth but reorganize for readability:
  - summary first
  - evidence and quant details second
  - raw/deep internals last
- Surface analysis mode state and explicit upgrade path:
  - current mode label (`lightweight`/`deep`)
  - `Run Deep Analysis` action

### Analysis Observation Lab (Internal Tool)
- Keep `/demo/analysis` as non-primary, internal-facing workflow observability UI.
- Use for pipeline debugging, payload inspection, and execution timeline verification.

## 4) Module Function Contracts (v1)

### Module A - Portfolio Builder Module
- Input: selected symbols + optional weights.
- Output: ordered positions with editable weights.
- Responsibilities:
  - default weight assignment on add
  - weight edit/remove interactions
  - local-save hydration and persistence

### Module B - Portfolio Metrics Module
- Input: current portfolio positions + latest per-symbol projections.
- Output:
  - `portfolioRiskScore`
  - `expectedReturnRange`
  - `sectorConcentrationWarning`
- Responsibilities:
  - recompute on portfolio change
  - provide freshness/confidence hint

### Module C - Candidate Feed Module
- Input: seeded symbol universe + projection snapshots.
- Output: sortable/filterable card list for portfolio actions.
- Responsibilities:
  - cache-first card render
  - freshness badge render
  - drag/add and `more` entry points

### Module D - Stock Detail Module
- Input: selected symbol + latest projection/artifacts.
- Output: organized detail sections with mode action control.
- Responsibilities:
  - readable information hierarchy
  - explicit `Run Deep Analysis` escalation
  - non-blocking refresh state display

### Module E - Analysis Mode Controller
- Input: symbol + user mode selection.
- Output: workflow trigger policy selection.
- Responsibilities:
  - lightweight default path
  - deep explicit path
  - mode status communication in UI

### Module F - Freshness and Cache Policy Module
- Input: latest projection metadata (`updated_at`, freshness window).
- Output: cache/fresh/stale state for UI + trigger policy.
- Responsibilities:
  - return cached state immediately
  - label `last updated`
  - refresh stale data without blanking current view

## 5) Implementation Stages (Detailed)

### Stage P0 - Product Reframe and Contract Alignment
Goal: make portfolio-home the canonical primary UX and demote analysis page to internal lab.
- Update docs and contracts to reflect product hierarchy.
- Define/lock `PortfolioSummaryViewModel` fields:
  - `portfolioRiskScore`
  - `expectedReturnRange`
  - `sectorConcentrationWarning`
  - `metricsFreshness`
- Confirm lightweight/deep mode semantics in API surface and UI copy.
- Canonical mapping:
  - `frontend/src/app/demo/analysis/page.tsx` (internal-role clarity)
  - `backend/app/routers/workflow.py`
  - `backend/app/workflows/analysis/projections/normalizer.py`

### Stage P1 - Portfolio Home Skeleton
Goal: deliver visible portfolio-first layout and interactions.
- Implement left/right two-panel UX with drag/add path.
- Add default-weight behavior on stock add.
- Add local-save restore path for working portfolio.
- Keep stock cards cache-first with freshness badge.
- Canonical mapping:
  - `frontend/src/app/demo/analysis/page.tsx` (until dedicated route split)
  - `frontend/src/components/*` (moduleized UI extraction)

### Stage P2 - Portfolio Metrics and Candidate Feed
Goal: make portfolio decisions actionable in under two minutes.
- Compute and render three mandatory metrics.
- Add candidate feed ranking/filter behavior suitable for quick add.
- Ensure metrics recompute on weight/position edits.
- Canonical mapping:
  - `backend/app/workflows/analysis/projections/store.py`
  - `backend/app/routers/workflow.py`
  - `frontend/src/app/demo/analysis/page.tsx`

### Stage P3 - Detail Reorganization + Deep Escalation
Goal: keep rich detail while improving readability and explicit depth control.
- Reorganize `more` detail into summary/evidence/deep sections.
- Add explicit deep-mode action with clear progress state.
- Keep stale data visible while refresh/deep runs in background.
- Canonical mapping:
  - `frontend/src/app/demo/analysis/page.tsx`
  - `backend/app/workflows/analysis/orchestrator.py`
  - `backend/app/routers/workflow.py`

### Stage P4 - Internal Observation Lab Hard Boundary
Goal: ensure internal tooling does not define product UX direction.
- Keep advanced workflow internals in lab-only context.
- Add clear labeling/route intent for internal-only usage.
- Maintain parity checks so lab can validate engine behavior.
- Canonical mapping:
  - `frontend/src/app/demo/analysis/page.tsx`
  - internal docs and runbooks

## 6) Acceptance Criteria by Stage

- P0: product docs and contracts unambiguously define portfolio as primary UX.
- P1: user can add/edit portfolio positions and recover local state after refresh.
- P2: user sees risk/return/concentration updates from current portfolio edits.
- P3: user can inspect organized stock detail and explicitly trigger deep analysis.
- P4: analysis lab is clearly internal and no longer treated as primary product flow.

## 7) Deferred (Explicitly Not in This Milestone)

- Auth/rbac/quota hardening for production.
- Full account-backed portfolio persistence and sharing.
- Fully automated optimizer/rebalancer recommendations.
- Full-market screener UX and broad-universe ranking.

## 8) Open Decisions (Explicit Defaults)

- Default weight on add: unresolved (`5%` proposed default).
- Portfolio risk/return formulas: heuristic v1 vs model-backed v1.1.
- Candidate feed default sort: quality-first vs portfolio-impact-first.
- Seed refresh policy for initial ~50 symbols: manual reseed vs scheduled refresh.

## 9) Canonical Files for Execution

- Roadmap and execution status: `./roadmap.md`
- Architecture target state: `./architecture.md`
- Decision rationale: `./architecture-decisions.md`
- Active blockers: `./debuglog.md`
