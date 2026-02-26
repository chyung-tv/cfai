# Debug Log

Purpose: track active bugs, attempts, outcomes, and next actions.

## Active Bugs

Use one entry per active bug.

#### [MOD1-VAL-001] Validation tools unavailable in current environment
- Status: `active`
- Scope: frontend validation for `frontend`
- Repro steps:
  1. Run `npm --prefix frontend run check-types`
  2. Run `npm --prefix frontend run lint`
- Expected: TypeScript and ESLint checks execute for edited frontend files.
- Actual: shell returns `tsc: command not found` and `eslint: command not found`.
- Root-cause hypothesis: local dependencies are not installed in `frontend` (or PATH is missing local binaries).
- Attempt history:
  - 2026-02-26 00:00 - fixed wrapper script invocation (`run check-types`) - still blocked by missing binaries.
- Next attempt:
  - Install frontend dependencies (`npm --prefix frontend install`), then rerun checks.
- Owner: user + coding agent

#### [MOD1-CLEANUP-001] Residual legacy Motia references outside active runtime paths
- Status: `active`
- Scope: archival docs/tests/lockfiles still containing `motia` strings
- Repro steps:
  1. Search for `motia dev` / `next-auth` / `@repo/db` references repo-wide.
  2. Observe matches in non-runtime legacy files.
- Expected: no legacy references in active runtime paths.
- Actual: references remain in archival docs/lockfiles (for example `.github/copilot-instructions.md` and legacy lockfiles).
- Root-cause hypothesis: Module 1 cutover prioritized executable/runtime paths; non-executable legacy artifacts remain.
- Attempt history:
  - 2026-02-26 00:00 - removed runtime ownership paths and deployment/docs core files - residual archival references remain.
  - 2026-02-26 00:00 - migrated `apps/web` -> `frontend` and deleted `apps/backend`; reduced path-drift references, archival mentions still remain in selected non-runtime files.
- Next attempt:
  - Decide whether to purge all legacy docs/tests now or defer to a dedicated cleanup sweep.
- Owner: user + coding agent

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

### Template

#### [BUG-ID] Short title
- Resolved on:
- Resolution summary:
- Preventive note:
- Related memo: `./memo.md#...`
