---
name: brainstorm
description: Entry point for any feature idea or non-trivial change. Sharpens a vague idea through grilling, explores it via ce-brainstorm, then hands off into /plan. Use when the user describes a feature, an idea, a problem to solve, or says "let's brainstorm".
---

# Brainstorm

Resolve repository-relative paths from the repository root.

Repo wrapper around `ce-brainstorm`. This file is the team's contract; the underlying tool may change, this contract does not.

## Dependency check (first, always)

Required skill: `ce-brainstorm` (compound-engineering plugin). If it is not in your available skills list: **STOP immediately.** Tell the user:

> Missing skill: `ce-brainstorm`. Install or enable the compound-engineering plugin, then re-run this workflow.

Then end the turn. Resume only after the user confirms installation.

## Flow

1. **Sharpen.** If goal, non-goals, or constraints are ambiguous, grill the human first. Architecture decomposition and requirements are the human's call; extract and sharpen them, do not invent them. Skip this step only when the idea is already crisp.
2. **Brainstorm.** Invoke `ce-brainstorm` with the sharpened idea as input.
3. **Hand off.** When the brainstorm produces a requirements picture, continue directly into the `/plan` skill with the result.
