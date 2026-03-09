# Debug Log

Purpose: only unresolved, reproducible blockers that can stall roadmap progress.

## Active

### [MOD3-POLICY-001] Quota enforcement missing on analysis trigger
- Status: `active`
- Scope: backend policy boundary (`/analysis/trigger`)
- Repro:
  1. inspect backend app for quota guard
  2. no quota dependency/middleware exists
- Expected: auth -> role -> quota sequence enforced for trigger flows.
- Actual: auth exists; quota layer is absent.
- Next: implement quota guard contract and wire it in trigger path.
- Owner: user + coding agent

### [MOD3-POLICY-002] Analysis read/event route auth policy is undefined in code
- Status: `active`
- Scope: `/analysis/latest`, `/analysis/events`, `/analysis/events/stream`
- Repro:
  1. inspect workflow router dependencies
  2. endpoints above can be called without `require_auth`
- Expected: explicit and consistent policy decision (public or auth-required) with enforcement.
- Actual: policy is implicit and inconsistent with Module 3 acceptance intent.
- Next: decide policy and enforce in router.
- Owner: user + coding agent

## Recently Resolved

- [MOD2-DEVX-001] Frontend compose reinstall loop fixed by guarded install + stable pnpm store.
- [MOD1-VAL-001] Validation/tooling mismatch superseded by re-baseline.
- [MOD1-CLEANUP-001] Legacy Motia references no longer runtime blockers.

For reusable lessons, see `./memo.md`.

