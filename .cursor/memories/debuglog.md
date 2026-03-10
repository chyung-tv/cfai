# Debug Log

Purpose: only unresolved, reproducible blockers that can stall roadmap progress.

## Active

- None.

## Recently Resolved

- [MOD2-DEVX-001] Frontend compose reinstall loop fixed by guarded install + stable pnpm store.
- [MOD1-VAL-001] Validation/tooling mismatch superseded by re-baseline.
- [MOD1-CLEANUP-001] Legacy Motia references no longer runtime blockers.
- [MOD3-LLM-001] Dev flash-lite model ID mismatch caused deep-research 404; resolved by aligning env to `gemini-3.1-flash-lite-preview` and recreating backend container.
- [MOD3-POLICY-001] Quota/auth policy hardening is explicitly deferred by local-first milestone execution policy; not an active blocker during core slice delivery.
- [MOD3-PIPE-001] Advisor validation failure no longer crashes persistence path; `error_message` write is DB-safe and advisor schema minimums were relaxed for local-first stability.

For reusable lessons, see `./memo.md`.

