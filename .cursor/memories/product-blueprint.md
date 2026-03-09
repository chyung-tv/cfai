# CFAI Product Blueprint (Canonical)

Last validated: 2026-03-09  
Purpose: single canonical reference for product intent, UX shape, staged delivery, and acceptance.

## 1) Problem We Are Solving

Turn one-click stock analysis into a decision-support research hub:
- run or reuse analysis for a symbol
- show a clear top-level summary first
- allow drill-down into deep reasoning and raw detail
- support lightweight cross-symbol comparison as a stepping stone to future screening

## 2) Product Intent (Agreed)

- Primary mode: structured research hub (not auto-trading recommendation engine).
- v1 output style: evidence-first; no explicit final buy/hold/avoid verdict.
- Summary priority: business quality first, then valuation legitimacy, then thesis.
- Trigger behavior: staleness-window policy (reuse fresh result, refresh stale result).
- Compare mode: ranked sortable table for analyzed symbols.
- Default compare rank: quality first, then valuation legitimacy.

## Canonicality Rule

- Product behavior, UX hierarchy, and rollout stages must be defined here first.
- `roadmap.md` tracks execution status only and should not restate product specs.
- `architecture.md` tracks system design only and should reference this file for product-facing behavior.
- `architecture-decisions.md` records rationale/decision records only and should not duplicate UX specs.

## 3) Core UX Shape

### Single-Stock Research Hub
- Symbol input with one-click analysis request.
- Top summary blocks (must-have):
  - investment thesis
  - business quality
  - valuation legitimacy
- Drill-down tabs:
  - deep research narrative/citations
  - quant details (`reverse_dcf`, growth audit)
  - detailed payload inspector
- Live run visibility:
  - status/substate and timeline during execution

### Compare View (Lightweight)
- Table over analyzed symbols only.
- Sortable columns (v1):
  - symbol
  - business quality tier
  - valuation legitimacy
  - risk proxy count
  - last updated
- Row click opens symbol research hub detail.

## 4) Implementation Stages

### Stage 0 - Contract Freeze
Goal: lock a stable summary contract from existing projection payload.
- Define `SummaryViewModel` fields:
  - `investmentThesis`
  - `businessQuality`
  - `valuationLegitimacy`
  - `analysisFreshness`
- Keep `contract_version` discipline in projection normalizer.
- Dev/test LLM runtime policy for full workflow cost control:
  - deep-research node stays in workflow but defaults to `gemini3.1-flash-lite`
  - dev deep-research flash-lite path enables grounding by default (`DEEP_RESEARCH_DEV_GROUNDING_ENABLED=true`)
  - production may route deep-research node to deep-research endpoint while non-deep-research nodes remain flash-lite
- Canonical backend mapping:
  - `backend/app/workflows/analysis/projections/normalizer.py`
  - `backend/app/models/workflow/analysis_workflow_projection.py`
  - `backend/app/routers/workflow.py`

### Stage 1 - Research Hub Summary + Drill-Down
Goal: deliver the quality-first single-stock page experience.
- Render summary cards in priority order.
- Keep detail tabs and timeline visible.
- Handle incomplete payloads gracefully.
- Canonical frontend mapping:
  - `frontend/src/app/demo/analysis/page.tsx`

### Stage 2 - Staleness-Window Flow
Goal: improve one-click behavior and latency perception.
- Fetch latest projection.
- If fresh: return/show immediately.
- If stale: trigger refresh and stream progress; keep old summary visible until replaced.
- Canonical mapping:
  - `backend/app/routers/workflow.py`
  - `backend/app/workflows/analysis/orchestrator.py`
  - `frontend/src/app/demo/analysis/page.tsx`

### Stage 3 - Lightweight Compare
Goal: enable practical multi-symbol inspection before full screening.
- Add compare API over projection rows.
- Add sortable table UI with default ranking.
- Support quick drill-in to symbol detail page.
- Canonical mapping:
  - `backend/app/routers/workflow.py`
  - `backend/app/workflows/analysis/projections/store.py`
  - `frontend/src/app/demo/analysis/page.tsx`

### Stage 4 - Screening Foundations
Goal: prepare data model for future screening scale.
- Persist normalized compare keys in projection model.
- Ensure stable ordering semantics and retention baseline.
- Document transition to full screener module.
- Canonical mapping:
  - `backend/app/workflows/analysis/projections/normalizer.py`
  - `backend/app/models/workflow/analysis_workflow_projection.py`

## 5) Acceptance Criteria by Stage

- Stage 0: summary contract is explicit, versioned, and backward-safe.
- Stage 1: one stock can be analyzed and understood from summary without reading raw payload.
- Stage 2: stale/fresh behavior is predictable and visible in UI state.
- Stage 3: user can compare multiple analyzed symbols and open details quickly.
- Stage 4: compare model supports future screening without contract rewrite.

## 6) Deferred (Explicitly Not in This Milestone)

- Auth/rbac/quota hardening for production.
- Explicit portfolio optimizer/recommendation engine.
- Full-market screener UX and broad universe ranking.

## 7) Canonical Files for Execution

- Roadmap and execution status: `./roadmap.md`
- Architecture target state: `./architecture.md`
- Decision rationale: `./architecture-decisions.md`
- Active blockers: `./debuglog.md`
