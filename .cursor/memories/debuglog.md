# Debug Log

Purpose: track active bugs, attempts, outcomes, and next actions.

## Active Bugs

Use one entry per active bug.

### Template

#### [BUG-ID] Short title
- Status: `active` | `blocked` | `resolved`
- Scope: affected modules/files/features
- Repro steps:
  1. ...
  2. ...
- Expected:
- Actual:
- Root-cause hypothesis:
- Attempt history:
  - YYYY-MM-DD HH:MM - Attempt summary - Result
- Next attempt:
- Owner:

---

## Resolved Bugs (Recent)

Move finished items here with a short note and link to any lesson in `memo.md`.

#### [MOD2-DEVX-001] Frontend compose reinstall loop caused slow or faulty startup perception
- Resolved on: 2026-02-26
- Resolution summary: replaced forced `pnpm install --force` startup with guarded install-if-missing flow and set `PNPM_STORE_DIR=/pnpm/store`; frontend now reaches ready state immediately on restart once dependencies are present.
- Preventive note: avoid unconditional dependency reinstalls in container startup commands for hot-reload dev services.
- Related memo: `./memo.md#2026-02-26---frontend-compose-startup-stabilization-pnpm-store--no-reinstall-loop`

#### [MOD1-VAL-001] Validation tools unavailable in current environment
- Resolved on: 2026-02-26
- Resolution summary: superseded by frontend re-bootstrap and package-manager standardization (`pnpm` in `frontend`, `uv` in `backend`), with dependency install/run commands updated in `README.md`.
- Preventive note: after scaffold resets, retire stale validation bug entries and re-open only if reproducible on current toolchain.
- Related memo: `./memo.md#2026-02-26---frontend-rebootstrap-and-module-1-closure-rebaseline`

#### [MOD1-CLEANUP-001] Residual legacy Motia references outside active runtime paths
- Resolved on: 2026-02-26
- Resolution summary: treated as no longer blocking Module 1 closure after repository re-baseline; residual mentions are documentation-only and not runtime dependencies.
- Preventive note: evaluate legacy string references by runtime impact first, not by raw text-match count.
- Related memo: `./memo.md#2026-02-26---frontend-rebootstrap-and-module-1-closure-rebaseline`

### Template

#### [BUG-ID] Short title
- Resolved on:
- Resolution summary:
- Preventive note:
- Related memo: `./memo.md#...`
