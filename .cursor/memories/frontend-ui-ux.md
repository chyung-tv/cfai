# Frontend UI/UX Baseline

Last updated: 2026-02-26
Scope: `frontend` design system, layout patterns, interaction behavior, and state feedback conventions.

## Design System Foundation

- Stack: Next.js App Router + shadcn/ui + Radix primitives + Tailwind CSS v4.
- Theme model: CSS variables in `src/app/globals.css` with light/dark token pairs.
- Typography: Geist Sans + Geist Mono via `next/font`.
- Utility conventions:
  - class composition with `cn()` (`clsx` + `tailwind-merge`)
  - variants via `class-variance-authority` for reusable UI primitives
  - iconography via `lucide-react`

## Core Visual Language

- Primary shell style:
  - sticky top header with blur and translucent background
  - centered content using `container mx-auto` and responsive `max-w-*` wrappers
- Surface primitives:
  - `Card`, `Table`, `Badge`, `Button`, `Input`, `Tabs`, `Tooltip`, `Separator`
- Color behavior:
  - semantic status colors for analysis lifecycle (green completed, blue processing, red failed, amber access warning)
  - dark mode support applied through tokenized variables rather than hardcoded colors

## Information Architecture

- Route groups:
  - `(marketing)`: landing and login surfaces
  - `(app)`: authenticated/working surfaces (dashboard, analysis)
- Shared top-level behavior:
  - marketing and app both preserve consistent branding and typography
  - app shell includes `AppHeader` with symbol search and navigation

## Primary UX Flows

- Stock search as global entrypoint:
  - reusable `StockSearchBar` in two modes (`hero`, `compact`)
  - uppercase normalization and direct route transition to `/analysis/[symbol]`
- Analysis lifecycle UX:
  - no cached result: show `AnalysisLoading`, trigger backend workflow, poll stream status
  - cached/completed result: render full report immediately
  - progressive feedback messages shown while polling events
- Dashboard workflow UX:
  - summary stats + history table + per-row actions (`view`, disabled processing, `retry`)
  - relative-time labels for recent activity

## Feedback and State Conventions

- Loading:
  - spinner-first visual language (`Loader2`) for page and row-level pending states
- Error:
  - explicit error state with icon, concise message, and recovery CTA
- Access gating:
  - amber warning banner for no-access users while preserving read-only history visibility
- Notifications:
  - global `sonner` toaster provider mounted in app providers

## Reuse Rules for Future UI Work

- Reuse existing shadcn primitives before adding custom base components.
- Keep spacing/layout conventions aligned to existing container + card rhythm.
- Keep status semantics consistent across dashboard, analysis loading, and report header.
- Prefer token-based styling and existing variant systems over one-off CSS.

## Related Memory Links

- Related roadmap: `./roadmap.md#module-4-frontend-adaptation-readability-and-ux-integration`
- Related memo entry: `./memo.md#2026-02-26---frontend-uiux-baseline-extraction-and-backend-uv-standardization`
