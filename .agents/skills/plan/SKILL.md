---
name: plan
description: Turn a brainstorm result or feature request into a visual, human-reviewable plan in docs/plans/draft/, then put it through a blind adversarial challenge round before a human ever sees it. Use after /brainstorm, or when the user says "plan this", "write a plan", "how should we build this".
---

# Plan

Resolve repository-relative paths from the repository root.

Repo wrapper around `ce-plan`. This file is the team's contract; the underlying tool may change, this contract does not.

## Dependency check (first, always)

Required skill: `ce-plan` (compound-engineering plugin). If it is not in your available skills list: **STOP immediately.** Tell the user:

> Missing skill: `ce-plan`. Install or enable the compound-engineering plugin, then re-run this workflow.

Then end the turn. Resume only after the user confirms installation.

## Flow

1. **Plan.** Invoke `ce-plan` to produce a diagram-first plan in `docs/plans/draft/`.
2. **Challenge round.** The plan goes through a blind adversarial challenge: a fresh-context reviewer attacks the plan, the writing agent adjudicates every finding, one rebuttal round, contested items go to the human.
3. **Hard stop.** Present the plan to the human. Do NOT proceed to implementation until explicit approval.

## Preconditions

- Read AGENTS.md for project structure and conventions before planning.
- Plans go to `docs/plans/draft/` with YAML frontmatter (`title`, `status: draft`, `created`).
- Move to `active/` when implementation starts, `done/` when finished.
