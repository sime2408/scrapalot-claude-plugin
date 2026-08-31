---
description: Sync README documentation in docs/ folders with current codebase state
allowed-tools: Bash, Read, Edit, Grep, Glob
---

## Context

Documentation lives in `docs/` folders within each subproject:
- `scrapalot-chat/docs/README_*.md`
- `scrapalot-backend/docs/README_*.md`
- `scrapalot-ui/docs/README_*.md`

Root CLAUDE.md at `/opt/scrapalot/CLAUDE.md` is the master reference (~335 lines).

## Your Task

Update README documentation to match current code.

### Steps

1. Ask user which subproject to sync (chat/backend/ui/all)
2. **Mechanical lint pre-pass (run first — it builds your checklist).**
   Run the deterministic drift detector before reading anything by hand:
   ```bash
   python3 .claude/scripts/doc_sync_lint.py <chat|backend|ui|gw|all>
   ```
   It extracts every source path each README cites, resolves it against ALL
   subproject roots (so a cross-repo citation is not a false positive), skips
   template/example placeholders, and reports only genuinely **dead
   references** — cited files that no longer exist anywhere. It also surfaces
   numeric **count claims** ("21 strategies") next to where they appear.
   - Treat the DEAD list as the authoritative starting checklist. For each,
     find where the file moved/was renamed (`git log --follow`, grep for the
     basename) and fix the citation — or delete the mention if the thing is
     gone. Do NOT touch the skipped example paths.
   - Count claims are **advisory, not auto-judged** — verify each against code
     and the root CLAUDE.md before changing. Divergent numbers across READMEs
     (e.g. one file says 21, another 30) are a signal to reconcile, not proof.
3. For each target subproject:
   a. List all `docs/README_*.md` files
   b. Read each README and identify what it documents
   c. Cross-reference with actual code (the pre-pass covers paths + counts
      mechanically; here you cover what it can't):
      - Confirm/repair every DEAD path from step 2
      - Check class/function names are current
      - Check architecture descriptions match current flow
   d. List discrepancies found
4. Present a summary of what needs updating per file
5. After user approval, apply changes with Edit tool
6. Do NOT create new README files unless explicitly asked

### Guardrails

- Ask user permission before creating any new *.md files
- Preserve existing document structure and formatting style
- Only update factual content (counts, paths, names) — don't rewrite prose
- Cross-check counts against root CLAUDE.md "Verified Code Counts" section
- Do NOT update root CLAUDE.md — that's maintained separately
- Commit changes only when user asks
