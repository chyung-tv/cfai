# CFAI Roadmap

Last validated: 2026-03-18 (workspace/memory reality check)
Purpose: single progress tracker for the pivot to Portfolio Co-Pilot Canvas.

## Session Briefing (mandatory order)

1. Where we are at
2. What we need to implement next
3. What we just implemented

- Where we are at: split-screen workspace and copilot APIs are live; chat streams through `AgentRuntime`, and document tools (`create_document`, `edit_document`) execute directly behind skill allowlists.
- What we need to implement next: add explicit proposal/approval flow for AI document edits (or ratify direct-apply as an ADR) so product intent and runtime behavior are aligned.
- What we just implemented: memory/skills/rules CRUD, workspace snapshots + restore, and memory-job notifications were integrated into the copilot workspace loop.

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
- [ ] Module 10 - Proposal/approval alignment for document edits

## Current Focus

- Active slice: post-cutover runtime hardening on new copilot paths only.
- Active slice: alignment between product intent (approval-gated edits) and runtime behavior (direct tool-applied edits).
- Active slice: keep deep research tool path disabled/placeholder while chat path stabilizes.
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

### Stage C8 - Workspace Surface Expansion
Status: `completed`
- Add workspace snapshots (create/list/restore) for documents + skills + rules + memory state.
- Add skills/rules/memory CRUD APIs and wire them into the right-pane editor workflow.
- Add memory-job processing + notification SSE stream for asynchronous memory writes.

### Stage C9 - Proposal/Approval Contract Alignment
Status: `in_progress`
- Current behavior: `edit_document` executes within chat turn when skill policy allows.
- Next requirement: introduce explicit AI edit proposal object + user approval apply path, or formally accept direct-apply in ADR + blueprint updates.

## Acceptance Gates

- User can open default route and see split workspace (chats/chat/document/docs rails).
- User can submit prompt and receive streaming assistant output with tool execution metadata.
- Canonical docs/rules/skills/memory can be edited and persisted from the workspace.
- Snapshot create/list/restore works for workspace state persistence.
- Open gap: explicit proposal->approval->apply loop for AI document edits is not yet implemented.
