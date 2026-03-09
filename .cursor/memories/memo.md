# Memo

Purpose: capture solved problems, reusable fixes, and lessons learned.

## Lessons Index

- Add short links to entries for quick recall.

## Entry Template

### YYYY-MM-DD - Topic
- Context:
- What worked:
- What failed:
- Final fix:
- Why it worked:
- Reuse guidance:
- Anti-pattern to avoid next time:
- Related bug log: `./debuglog.md#...`
- Related roadmap item: `./roadmap.md#...`

---

## Example Placeholder

### 2026-02-26 - Memory system bootstrap
- Context: initialized `.cursor/memories` and `.cursor/rules`.
- What worked: defined clear templates and links across docs.
- What failed: n/a
- Final fix: use one source-of-truth per workflow (`roadmap`, `debuglog`, `memo`).
- Why it worked: reduced ambiguity for future implementation sessions.
- Reuse guidance: copy the template for every major fix.
- Anti-pattern to avoid next time: storing active bug details in ad-hoc chat only.

### 2026-02-26 - New-agent workflow contract
- Context: standardize how each fresh agent session starts.
- What worked: enforce a fixed briefing sequence plus module-level planning handoff.
- What failed: n/a
- Final fix: require status output order: where we are at -> what we need next -> what we just implemented.
- Why it worked: gives immediate context continuity before detailed planning.
- Reuse guidance: keep `Session Briefing` in `roadmap.md` current after each meaningful change.
- Anti-pattern to avoid next time: jumping into coding before status alignment and module planning.

### 2026-02-26 - Pre-prune workflow capture before hard cutover
- Context: needed to remove Motia runtime while preserving backend behavior knowledge for rewrite parity.
- What worked: documented the full event chain, stream lifecycle, and persistence touchpoints before deletion.
- What failed: relying on memory-only understanding of step sequencing.
- Final fix: captured backend workflow parity baseline and later integrated it into `./architecture.md` as durable architecture context.
- Why it worked: made destructive cleanup safer and gave a concrete parity checklist for FastAPI migration.
- Reuse guidance: for any hard cutover, document trigger/transition/persistence semantics first, then prune.
- Anti-pattern to avoid next time: deleting runtime artifacts before a durable behavioral spec exists.
- Related bug log: `./debuglog.md#mod1-cleanup-001-residual-legacy-motia-references-outside-active-runtime-paths`
- Related roadmap item: `./roadmap.md#module-1-hard-cutover-and-pruning`

### 2026-02-26 - Physical executable-root migration
- Context: after cutover refactors, repository still had app code under `apps/web` while target structure requires `/frontend` and `/backend`.
- What worked: moved full web app tree into `frontend`, deleted legacy-only `apps/backend`, and corrected moved-path build schema references.
- What failed: leaving old path assumptions in docs/debug notes caused drift.
- Final fix: updated operational docs/rules/memory entries to reference `frontend` and `backend` as canonical roots.
- Why it worked: eliminated structural ambiguity and made acceptance criteria verifiable at the filesystem level.
- Reuse guidance: when restructuring roots, do physical moves early and immediately update docs/memory references in the same wave.
- Anti-pattern to avoid next time: keeping wrapper indirection longer than necessary once direct migration is safe.
- Related bug log: `./debuglog.md#mod1-cleanup-001-residual-legacy-motia-references-outside-active-runtime-paths`
- Related roadmap item: `./roadmap.md#module-1-hard-cutover-and-pruning`

### 2026-02-26 - Frontend UI/UX baseline extraction and backend uv standardization
- Context: needed to preserve current design behavior before deeper frontend adaptation while removing mixed backend package management paths.
- What worked: documented concrete primitives, layout patterns, route-group UX flow, and status-feedback conventions from `frontend` into a dedicated memory artifact.
- What failed: relying on default generated README/package-manager assumptions did not reflect current runtime reality.
- Final fix: documented frontend UI/UX baseline and moved backend dependency management to `uv` via `backend/pyproject.toml` (removing `backend/requirements.txt` and `backend/package.json`); the UI/UX baseline is now integrated into `./architecture.md`.
- Why it worked: creates a stable UX reference for Module 4 and a single Python package manager contract for backend execution.
- Reuse guidance: for migration-phase UI work, snapshot current interaction/state conventions first; for Python services, keep install/run workflows centered on `uv sync` and `uv run`.
- Anti-pattern to avoid next time: splitting backend dependency/runtime commands across `requirements.txt`, npm scripts, and ad-hoc Python invocations.
- Related roadmap item: `./roadmap.md#module-4-frontend-adaptation-readability-and-ux-integration`

### 2026-02-26 - Frontend rebootstrap and Module 1 closure rebaseline
- Context: frontend was re-scaffolded, invalidating parts of the previous migration narrative and active Module 1 bug context.
- What worked: performed a criteria-first check (runtime dependency paths, executable boundaries, active manifests) before deciding module closure.
- What failed: leaving old migration/bug wording in memories and README created planning drift after the reset.
- Final fix: closed Module 1 in roadmap, moved Module 1 debug items to resolved, and refreshed README to match the new baseline.
- Why it worked: re-aligned planning artifacts with the actual filesystem/runtime state, reducing false blockers.
- Reuse guidance: after major scaffolding resets, immediately re-baseline roadmap/debug/docs before coding the next module.
- Anti-pattern to avoid next time: carrying old module blockers forward without re-validating them against the new project shape.
- Related bug log: `./debuglog.md#resolved-bugs-recent`
- Related roadmap item: `./roadmap.md#module-2-containerized-runtime-foundation-docker--postgresql`

### 2026-02-26 - Module 2 docker hot-reload and async migration baseline
- Context: Module 2 required a strong local developer experience with frontend/backend bind mounts plus database migration discipline.
- What worked: defined compose services for frontend/backend/postgres with named dependency volumes and reload commands, while keeping Alembic execution manual.
- What failed: older env/docs assumed host-run only workflow and sync DB assumptions.
- Final fix: introduced docker-first runbook, async SQLAlchemy session foundation, Alembic async env wiring, and an initial migration for `health_probes`.
- Why it worked: aligned runtime, dependency management (`uv`), and schema evolution into one repeatable local workflow.
- Reuse guidance: for new backend modules, add ORM models under `app/models`, then generate/apply migrations manually via compose one-off commands.
- Anti-pattern to avoid next time: auto-running migrations on API start in shared dev environments.
- Related roadmap item: `./roadmap.md#module-2-containerized-runtime-foundation-docker--postgresql`

### 2026-02-26 - Frontend compose startup stabilization (pnpm store + no reinstall loop)
- Context: frontend container appeared faulty after restarts because startup command reinstalled dependencies every boot and could stall on slow registry/network.
- What worked: removed forced reinstall behavior and switched startup logic to install only when `node_modules` is absent.
- What failed: `pnpm install --force` at startup caused repeated module recreation and delayed app readiness.
- Final fix: updated compose env (`PNPM_STORE_DIR=/pnpm/store`) and command guard, confirmed restart readiness with frontend `200` and backend `/health` + `/health/db` status `ok`.
- Why it worked: bind-mount hot reload stayed intact while dependency install became a one-time setup, dramatically improving restart DX.
- Reuse guidance: for containerized JS dev servers, separate source bind mounts from dependency volume initialization and avoid forced reinstalls in steady state.
- Anti-pattern to avoid next time: coupling every container boot to a full dependency reinstall.
- Related bug log: `./debuglog.md#mod2-devx-001-frontend-compose-reinstall-loop-caused-slow-or-faulty-startup-perception`
- Related roadmap item: `./roadmap.md#module-2-containerized-runtime-foundation-docker--postgresql`

### 2026-03-02 - Workflow legacy purge and canonical package cutover
- Context: backend workflow refactor introduced new canonical paths, but temporary wrappers (`app/workflow`, `app/maintenance`, legacy model wrappers) remained and created ambiguity.
- What worked: moved real implementations into `app/workflows/analysis` and `app/workflows/maintenance`, centralized shared runtime in `app/core/workflow`, then deleted wrapper trees after import/lint/runtime validation.
- What failed: adapter-on-adapter layering initially caused duplication confusion and one circular-import issue in package initializers.
- Final fix: removed legacy files entirely and kept only canonical imports under `app/workflows/*`, `app/core/workflow/*`, and `app/models/workflow/*`; validated with backend import checks and workflow runs.
- Why it worked: one source-of-truth per domain/runtime concern eliminated path drift and reduced future refactor risk.
- Reuse guidance: during staged migrations, set a short compatibility window and record a hard cutoff task to physically delete adapters once validation passes.
- Anti-pattern to avoid next time: leaving compatibility wrappers in place after canonical paths are already stable.
- Related roadmap item: `./roadmap.md#module-3-backend-core-fastapi-workflow-auth-rbac-quota`

### 2026-03-04 - Projection read-model normalization boundary
- Context: ADR-0008 implementation required a frontend-optimized projection table while node payload shapes remain flexible and evolve over time.
- What worked: introduced a single projection normalizer at write time, versioned the contract (`contract_version`), and kept source artifacts/events as replayable truth.
- What failed: relying on raw large JSON alone creates drift risk between node outputs and UI read expectations.
- Final fix: added `analysis_workflow_projections` plus normalized payload composition on transition/artifact writes and switched `/analysis/latest` to projection-backed reads.
- Why it worked: decouples node-internal evolution from frontend contract stability without losing audit/reprojection capability.
- Reuse guidance: for read-model tables, normalize once at projection boundary and carry explicit contract versioning from day one.
- Anti-pattern to avoid next time: forcing every node to emit UI-ready schema directly.
- Related roadmap item: `./roadmap.md#34-persistence-and-cache-submodule`

### 2026-03-04 - Compose migration command uses uv-run Alembic
- Context: after backend runtime standardization on `uv`, direct `alembic` command inside compose run did not resolve in PATH.
- What worked: executing migration commands via `docker compose run --rm backend uv run alembic ...`.
- What failed: `docker compose run --rm backend alembic upgrade head` (`executable file not found in $PATH`).
- Final fix: updated operator runbook/README migration commands to use `uv run alembic` consistently.
- Why it worked: aligns migration execution with backend dependency/runtime manager and container environment.
- Reuse guidance: when backend is managed by `uv`, wrap tool invocations (`alembic`, scripts) with `uv run`.
- Anti-pattern to avoid next time: mixing host/global tool assumptions into containerized Python workflows.
- Related roadmap item: `./roadmap.md#module-2-containerized-runtime-foundation-docker--postgresql`
