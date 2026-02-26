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
