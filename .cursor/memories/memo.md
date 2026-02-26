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
- Final fix: created `.cursor/memories/backend-analysis-workflow.md` as the baseline contract before pruning.
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
- Final fix: created `./frontend-ui-ux.md` and moved backend dependency management to `uv` via `backend/pyproject.toml` (removing `backend/requirements.txt` and `backend/package.json`).
- Why it worked: creates a stable UX reference for Module 4 and a single Python package manager contract for backend execution.
- Reuse guidance: for migration-phase UI work, snapshot current interaction/state conventions first; for Python services, keep install/run workflows centered on `uv sync` and `uv run`.
- Anti-pattern to avoid next time: splitting backend dependency/runtime commands across `requirements.txt`, npm scripts, and ad-hoc Python invocations.
- Related roadmap item: `./roadmap.md#module-4-frontend-adaptation-readability-and-ux-integration`
