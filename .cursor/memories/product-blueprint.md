# CFAI Product Blueprint (Canonical)

Last validated: 2026-03-18
Purpose: canonical product definition for Portfolio Co-Pilot Canvas.

## Product Intent

- Build a split-screen co-editing workspace where user and AI manage one canonical portfolio workspace together.
- Treat the AI as a collaborative analyst and editor, not an auto-trading bot.
- Make canonical docs first-class:
  - state memory: portfolio ledger
  - alpha memory: strategy journal
  - philosophy memory: dynamic user rules

## Core UX

### Left Pane - Conversational Interface
- User chats with the agent.
- Agent explains reasoning, requests confirmation, and proposes edits.
- Streamed progress and responses are visible during runs.

### Right Pane - Canonical Documents
- Ledger and strategy journal are editable and persisted.
- AI edits are proposed first, then explicitly approved by user before write.
- Revision visibility is required for trust.

## MVP Scope (Locked)

- Split workspace route as default app entry.
- Chat turn API with streamed status.
- Deterministic proposed-edit format for canonical docs.
- Approve-and-apply edit flow with DB persistence.
- Session/thread + rules persistence.

## Out of MVP (Deferred)

- Broker API integration.
- OCR ingestion.
- Full automated optimizer/rebalancer.
- Production auth/rbac/quota hardening.

## Acceptance

- User can open workspace and complete one full loop:
  - prompt -> agent proposal -> approve edit -> persisted canonical docs.
- Reload shows latest ledger/journal/rules from backend storage.
- Product has no dependency on old portfolio-first route model.

## Current Implementation Reality

- Workspace/chat/memory/rules/skills/snapshots are implemented and persisted.
- AI tool calls currently apply document edits directly when skill policy permits.
- Explicit proposal -> approval -> apply UX remains the target contract and is tracked as the next alignment slice.
