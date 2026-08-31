---
description: Check and fix mobile layout issues for a given component
allowed-tools: Bash, Read, Edit, Grep, Glob, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__resize_window, mcp__claude-in-chrome__get_page_text, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__computer, mcp__claude-in-chrome__find, mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__javascript_tool
---

## Context

Scrapalot UI uses React 18 + Radix UI + Tailwind CSS. Mobile breakpoints:
- `isMobileOrTablet`: `window.innerWidth < 1080`
- `useIsMobile()` hook from `@/hooks/use-mobile`
- Dialogs should be fullscreen on mobile (see `knowledge-stacks-dialog.tsx` pattern)
- Buttons need `onMouseDown={(e) => e.preventDefault()}` to prevent focus loss on mobile

Key patterns in existing mobile-responsive components:
- `scrapalot-ui/src/components/knowledge/knowledge-stacks-dialog.tsx` — fullscreen dialog
- `scrapalot-ui/src/components/settings/settings.tsx` — mobile vs desktop tab layout
- `scrapalot-ui/src/components/layout/sidebar/` — mobile menu handling

## Your Task

Fix mobile layout for the component the user specifies.

### Steps

1. Read the target component source code
2. Open Chrome and resize to mobile viewport (390x844):
   - `mcp__claude-in-chrome__resize_window` with width=390, height=844
3. Navigate to the relevant page and screenshot the current state
4. Identify layout issues:
   - Overflowing content
   - Unreachable buttons (below fold or hidden)
   - Headers/toolbars that don't collapse properly
   - Dialogs that aren't fullscreen
   - Text truncation issues
5. Apply fixes following existing patterns:
   - Use `useIsMobile()` for conditional layouts
   - Make dialogs fullscreen on mobile
   - Collapsible sections for filters/toolbars
   - Stack horizontal layouts vertically
6. Rebuild: `npm run build` then `docker cp dist/. scrapalot-ui:/app/dist/`
7. Re-test in Chrome at mobile viewport to verify

### Guardrails

- Do NOT change desktop layout — only fix mobile
- Follow existing mobile patterns in the codebase (don't invent new approaches)
- Always test both light and dark themes
- Update BOTH translation files (en, hr) if adding new i18n keys
- Ensure touch targets are at least 44x44px
