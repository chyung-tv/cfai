# Rules Overview

This folder contains active Cursor rules for implementation behavior.

## Rule Files

- `implementation-core.mdc` - always-on implementation guardrails and new-session status briefing order.
- `memory-discipline.mdc` - always-on memory update requirements.
- `design-system.mdc` - frontend/shared UI guidance for shadcn + Tailwind + MCP sourcing.

## Notes

- `.mdc` is used so Cursor can apply rules automatically.
- Keep rules concise and enforceable.
- Add new rules only when they solve repeated issues, not one-off preferences.
- Working loop anchor: brief -> plan -> implement -> validate -> record.
