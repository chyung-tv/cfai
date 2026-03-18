# CFAI Architecture Snapshot

Last validated: 2026-03-18
Purpose: target architecture for co-editing Canvas MVP.

## System Shape

- `frontend` (Next.js + shadcn + Tailwind): split-screen workspace with chat, document editor, explorer rails, and snapshot controls.
- `backend` (FastAPI): `/copilot/*` workspace/chat/document/rules/skills/memory APIs + SSE streaming.
- `postgres`: canonical docs, revisions, snapshots, conversation/memory, skills/rules, workflow traces/events/artifacts.

## Domain Modules

- Reusable runtime layer: `backend/app/core/workflow/*`.
- Agent runtime layer: `backend/app/agent/{runtime,registry,skills}` with skill-gated tool execution.
- Copilot domain: session/thread orchestration, document CRUD/revisions, snapshots, rules, skills, memory CRUD.
- Memory domain (new):
  - ledger document
  - strategy journal document
  - conversation thread/messages
  - dynamic philosophy rules

## Request Flow (MVP)

1. Frontend sends chat turn to `/copilot/chat/turn/stream`.
2. Backend builds `AgentTurnContext` (messages, docs, rules, memories, skills).
3. Agent streams tokens/events and may emit tool calls.
4. Runtime validates skill tool policy and executes allowed tools directly.
5. Backend persists turn messages and updated document revisions; memory jobs run asynchronously.

## Persistence Strategy

- Keep workflow events/artifacts as reusable observability primitive.
- Canonical docs + revisions are source of truth for user-visible workspace state.
- Workspace snapshots persist full editable state (documents/rules/skills/memory/summary) for restore.
- `copilot_edit_proposals` model exists but is currently not part of the active request flow.

## Deferred

- Explicit AI proposal/approval apply contract for document edits.
- Activate real research tool execution path (`run_research` is currently placeholder-disabled).
- OCR ingestion and broker sync.
- Production-grade policy hardening (auth/rbac/quota).
- Multi-portfolio/account model.

## References

- Execution tracker: `./roadmap.md`
- Decisions: `./architecture-decisions.md`
- Product blueprint: `./product-blueprint.md`
