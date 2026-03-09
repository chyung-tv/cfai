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
