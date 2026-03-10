# CFAI Roadmap

Last validated: 2026-03-09 (Stage 1 shipped + local-dev hardening and runtime fixes)
Purpose: single source of execution status and next actions.

## Session Briefing (mandatory order)

1. Where we are at
2. What we need to implement next
3. What we just implemented

- Where we are at: Modules 1-2 are complete; Stage 0 and Stage 1 are implemented with summary-first `/analysis/latest` UX active and usable in `/demo/analysis`.
- What we need to implement next: execute Stage 2 staleness-window flow (show latest immediately, refresh stale in background with visible progression).
- What we just implemented: local-dev hardening after Stage 1 (auth guard temporary bypass for core milestone, CORS alignment for localhost/0.0.0.0 origins, advisor schema strictness relaxation, and workflow failure persistence fix).

## Module Status

- [x] Module 1 - Hard cutover and pruning
- [x] Module 2 - Containerized runtime foundation
- [~] Module 3 - Backend core (workflow + auth/rbac/quota) *(active)*
- [~] Module 4 - Frontend adaptation *(active)*
- [ ] Module 5 - Phase 1 completion gate

## Reality Check (2026-03-09)

- Backend analysis workflow exists end-to-end: `resolve_query` -> `deep_research` -> `structured_output` -> `reverse_dcf` -> `audit_growth_likelihood` -> `advisor_decision`.
- Projection read model exists and `/analysis/latest` reads from `analysis_workflow_projections` with fallback.
- Maintenance seed domain exists with admin endpoints and run tracking.
- Frontend `/demo/analysis` exists with tabs-first IA and SSE timeline.
- Quota guard is not implemented in backend yet (explicitly deferred in local-first milestone).
- Auth/rbac guards are intentionally disabled across analysis and maintenance routes for local core milestone velocity; restore policy gates after core milestone completion.
- Analysis failure persistence no longer crashes on oversized error strings (`error_message` now safely truncated to DB column length).
- `/demo/analysis` usability polish applied (font token fix, compact pipeline chips, improved spacing/tab behavior).

## Current Focus

- Active slice: Product experience milestone (research hub + compare table).
- Owners: user + coding agent.
- Blockers: see `./debuglog.md`.

## Next Execution Queue

1. Execute Stage 2 from `./product-blueprint.md`:
   - implement staleness-window UX (show latest immediately, refresh stale in background)
2. Execute Stage 3 from `./product-blueprint.md`:
   - projection-backed compare endpoint + sortable table
3. Execute Stage 4 from `./product-blueprint.md`:
   - normalized compare keys and retention baseline
4. Run local acceptance checks per stage and record outcomes here.

## Phase Acceptance Gates

### Module 3 Gate
- Trigger path is stable for local use; policy hardening remains explicitly deferred in this milestone.
- Transitions persist and stream via SSE.
- Final artifacts/results are durable and queryable.

### Module 4 Gate
- Frontend trigger + live progress + blueprint-defined summary/drill-down rendering works from backend contracts only.
- UX remains readable and stable for partial/failed payloads.

### Module 5 Gate (Phase 1 complete)
- Research hub flow and lightweight compare flow both pass in one verified local runbook.

## Product Blueprint Reference

- Canonical blueprint: `./product-blueprint.md`
- This roadmap tracks execution status only; product definitions must live in blueprint.

## Working Loop (context-optimized)

1. **Brief** from this file in mandatory order.
2. **Plan** only the active slice (avoid broad refactors).
3. **Implement** focused changes.
4. **Validate** with targeted runtime checks.
5. **Record**:
   - progress here
   - rationale in `architecture-decisions.md` when decisions change
   - blockers in `debuglog.md`
   - reusable lessons in `memo.md`
