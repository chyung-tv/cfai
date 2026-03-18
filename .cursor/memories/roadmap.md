# CFAI Roadmap

Last validated: 2026-03-17 (chat live-call flag split from deep research)
Purpose: single progress tracker for the pivot to Portfolio Co-Pilot Canvas.

## Session Briefing (mandatory order)

1. Where we are at
2. What we need to implement next
3. What we just implemented

- Where we are at: split-screen workspace is live with Gemini streaming chat, and code now routes through the new slice boundaries directly.
- What we need to implement next: implement first real tool path (`edit_document`) behind explicit proposal approvals and deepen copilot service decomposition.
- What we just implemented: split chat live-call gating from deep-research gating (`CHAT_ENABLE_LIVE_CALLS` vs `DEEP_RESEARCH_ENABLE_LIVE_CALLS`) so test chat can hit Gemini Flash-Lite while deep research remains disabled.

## Module Status

- [x] Module 1 - `.cursor` reset and pivot baseline docs/rules
- [x] Module 2 - Canonical docs + memory persistence schema
- [x] Module 3 - Copilot API/domain cutover
- [x] Module 4 - Split-screen workspace UI cutover
- [x] Module 5 - Hard cleanup + validation
- [x] Module 6 - Agent runtime scaffold + streamed chat turn
- [x] Module 7 - Slice-oriented structure refactor scaffold (compat-preserving)
- [x] Module 8 - Slice-oriented cleanup (legacy path removal)
- [x] Module 9 - Runtime flag split (chat vs deep research live calls)

## Current Focus

- Active slice: hard cutover implementation (no legacy compatibility).
- Active slice: post-cutover agent maturation (direct reply path now streamed; tool execution path scaffolded).
- Active slice: post-cleanup stabilization on new slice paths only.
- Owners: user + coding agent.
- Blockers: none.

## Active Implementation Queue

### Stage C0 - Pivot Baseline
Status: `completed`
- Recreate `.cursor` memories/rules with fresh-start assumptions.
- Remove prior product-direction references from execution guidance.

### Stage C1 - Persistence Core
Status: `completed`
- Add canonical document tables for ledger and strategy journal.
- Add conversation thread/message and dynamic rules memory tables.

### Stage C2 - Backend Contract Cutover
Status: `completed`
- Replace old `/analysis/*` product contracts with copilot session/chat/document APIs.
- Keep reusable runtime/orchestrator/provider primitives.

### Stage C3 - Frontend Workspace
Status: `completed`
- Replace default route with split-screen co-editing workspace.
- Remove old portfolio and maintenance product routes.

### Stage C4 - Cleanup and Validation
Status: `completed`
- Delete stale legacy APIs/components.
- Run targeted backend/frontend validation commands.

### Stage C5 - Agent Chat Runtime (v1 direct reply)
Status: `completed`
- Add backend agent runtime/types/tool-registry scaffold.
- Add Gemini chat streaming provider adapter.
- Add SSE chat turn endpoint with persisted final assistant message/proposal.
- Update frontend to consume stream and render incremental tokens.

### Stage C6 - Architecture Refactor (Slice Scaffold)
Status: `completed`
- Introduce `app/agent/{runtime,registry}` and `app/tools/{reply,documents,research}` scaffolding.
- Introduce `app/copilot/{api,service}` as primary module boundary and route wiring through it.
- Add compatibility re-exports for legacy imports to avoid breakage during transition.

### Stage C7 - Architecture Refactor (Shim Removal)
Status: `completed`
- Remove `app/agents/*`, `app/workflows/copilot/*`, `app/routers/copilot.py`, and old provider shim path.
- Move frontend source-of-truth to `src/features/workspace/components/*` and `src/shared/api/*`.
- Delete old frontend workspace component path and old backend API client path.

## Acceptance Gates

- User can open new default route and see chat pane + canonical docs pane.
- User can submit prompt, review proposed edit, approve edit, and persist result.
- Canonical docs and memory are loaded from backend persistence.
- No legacy portfolio-first navigation remains.
