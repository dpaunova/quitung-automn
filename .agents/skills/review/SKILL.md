---
name: review
description: Run the repo's review protocol over a chosen scope — the whole branch, an uncommitted diff, or a single commit. Fresh-context correctness reviewers plus quality lenses. Use before pushing, before opening a PR, or when the user says "review this".
---

# Review

Resolve repository-relative paths from the repository root.

The implementing context NEVER counts as the review. Every reviewer is a fresh-context subagent that did not write the code.

## Scope selection (first, always)

Before dispatching any reviewer, resolve which scope this run covers:

1. If the `/review` invocation carried a scope argument, use it.
2. Otherwise ASK using `AskUserQuestion`. Do NOT infer.

Options:
- **Whole branch vs main** — before a push or PR.
- **Uncommitted diff** — during active work.
- **Last commit** — targeted post-commit look.

## Review process

### Correctness reviewer

One fresh-context subagent over the diff. Prompt includes:
- The plan being implemented (if any)
- The exact file list and diff
- Project conventions from AGENTS.md

Findings: `file:line`, severity (major/medium/minor), concrete failure scenario, concrete fix.

### Standards reviewer

Checks against project conventions:
- All UI text in Bulgarian
- No secrets in code
- Input validation at boundaries
- Tests cover the change
- No code comments unless WHY is non-obvious

## After review

1. Every finding is FIXED or explicitly WAIVED by the human.
2. Re-run `pytest` after fixes.
3. Report the tally: findings found/fixed/waived.
