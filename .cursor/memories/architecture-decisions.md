# CFAI Architecture Decisions

Last validated: 2026-03-17
Purpose: lean ADR list for the co-editing pivot.

## Status Keys

- `accepted`: active decision
- `superseded`: historical only

## Accepted ADRs

### ADR-0001 - Hard cutover with no compatibility layer
- Date: 2026-03-17
- Status: `accepted`
- Why: reduce transition drag and avoid dual-contract maintenance.
- Impact: remove old portfolio-first routes/APIs now.

### ADR-0002 - MVP is chat-plus-canonical-doc loop
- Date: 2026-03-17
- Status: `accepted`
- Why: fastest path to validate the new concept.
- Impact: prioritize split workspace, proposed edits, approval, persistence.

### ADR-0003 - Reuse workflow runtime/event primitives
- Date: 2026-03-17
- Status: `accepted`
- Why: runtime/event scaffolding is already reliable and useful for streaming/traceability.
- Impact: preserve `core/workflow` patterns while replacing product contracts.

### ADR-0004 - Canonical docs are product source of truth
- Date: 2026-03-17
- Status: `accepted`
- Why: co-editing requires explicit, persistent state and revision trail.
- Impact: ledger/journal/rules persistence is mandatory in MVP schema.

### ADR-0005 - Build-fast execution policy
- Date: 2026-03-17
- Status: `accepted`
- Why: user prefers speed with minimal ceremony.
- Impact: targeted validation only; avoid broad refactors beyond cutover needs.

### ADR-0006 - Skill-gated direct document tool execution (interim)
- Date: 2026-03-18
- Status: `accepted`
- Why: runtime now executes `create_document`/`edit_document` directly when loaded skill policies allow, enabling working end-to-end edits before proposal UX landed.
- Impact: current behavior diverges from approval-gated intent; either add proposal/apply flow next or supersede this ADR with a new explicit product decision.

## Open Decisions

- Auth/rbac/quota hardening schedule after MVP.
- Final policy for deep research invocation defaults in production.
- Revision history depth and retention policy for canonical docs.
- Final resolution for AI document edit contract: proposal/approval gate vs direct apply.

## References

- Architecture snapshot: `./architecture.md`
- Product blueprint: `./product-blueprint.md`
- Execution tracker: `./roadmap.md`
