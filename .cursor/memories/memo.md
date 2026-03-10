# Memo

Purpose: short reusable lessons only. Move active troubleshooting to `./debuglog.md`.

## High-Value Lessons

### 2026-02-26 - Keep one source per memory concern
- Use `roadmap.md` for status/next work only.
- Use `architecture*.md` for design and decisions only.
- Use `debuglog.md` for unresolved issues only.

### 2026-02-26 - Re-baseline immediately after scaffolding resets
- After major repo shape changes, refresh roadmap/debug/docs in the same session.
- Avoid carrying stale blockers forward without re-checking filesystem/runtime reality.

### 2026-02-26 - Docker dev services should avoid forced reinstalls
- Container boot should be fast and idempotent.
- Use guarded dependency install and persistent package caches/stores.

### 2026-03-02 - Delete migration wrappers after stabilization
- Temporary compatibility layers are useful briefly but create long-term drift.
- Set explicit removal checkpoints once canonical paths pass validation.

### 2026-03-04 - Normalize projection contracts at one boundary
- Keep source events/artifacts flexible, but emit one versioned UI contract for reads.
- Avoid making each workflow node emit UI-specific schema directly.

### 2026-03-04 - In `uv`-managed Python environments, run tools via `uv run`
- Keep migration/runtime commands aligned with package/runtime manager.

### 2026-03-09 - Gemini model IDs and env reload discipline
- Gemini model naming must match exact API model IDs (e.g., `gemini-3.1-flash-lite-preview`).
- A container restart may not reflect changed env-file values; recreate service (`docker compose up -d --force-recreate backend`) when validating env-driven model routing.
- For dev deep-research with flash-lite, keep grounding as an explicit env toggle to control cost/quality tradeoff without changing workflow shape.

### 2026-03-09 - Local dev CORS must include real browser origin variants
- When frontend is opened via `0.0.0.0`, backend CORS must explicitly allow `http://0.0.0.0:<port>` in addition to `localhost` and `127.0.0.1`.
- Validate preflight explicitly with `OPTIONS` requests before assuming trigger path is broken.

### 2026-03-09 - Failure persistence should be DB-column safe
- Runtime/validation exceptions can exceed `VARCHAR(500)` and cause secondary DB write failures.
- Truncate persisted error strings at write boundary to avoid masking primary workflow errors.

### 2026-03-09 - Strict schema minima can destabilize LLM-driven nodes
- Overly strict `min_length` constraints in advisor output schema can fail otherwise usable model responses.
- Keep local-first schema constraints permissive during core milestone; tighten after prompt/model reliability improves.
