# CFAI Architecture Snapshot

Last validated: 2026-03-17
Purpose: target architecture for co-editing Canvas MVP.

## System Shape

- `frontend` (Next.js + shadcn + Tailwind): split-screen workspace only.
- `backend` (FastAPI): copilot session/chat/document APIs + orchestration.
- `postgres`: canonical docs, memory, workflow traces/events/artifacts.

## Domain Modules

- Reusable runtime layer: `backend/app/core/workflow/*`.
- Copilot domain (new): session, turn orchestration, proposed edits, approval/apply.
- Memory domain (new):
  - ledger document
  - strategy journal document
  - conversation thread/messages
  - dynamic philosophy rules

## Request Flow (MVP)

1. Frontend sends chat turn.
2. Backend orchestrator runs nodes and emits progress events.
3. Agent returns structured proposed edit for canonical docs.
4. Frontend shows proposal and requests explicit approval.
5. Backend applies approved edit and persists revision.

## Persistence Strategy

- Keep workflow events/artifacts as reusable observability primitive.
- Canonical docs are source of truth for user-visible portfolio workspace.
- Proposed edits are stored before apply for auditability.

## Deferred

- OCR ingestion and broker sync.
- Production-grade policy hardening (auth/rbac/quota).
- Multi-portfolio/account model.

## References

- Execution tracker: `./roadmap.md`
- Decisions: `./architecture-decisions.md`
- Product blueprint: `./product-blueprint.md`
