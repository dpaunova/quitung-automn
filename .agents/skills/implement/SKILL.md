---
name: implement
description: Execute an approved plan from docs/plans/draft/, with a mandatory review-and-verify epilogue. Use after /plan is approved, or when the user says "implement the plan", "build it", "go ahead".
---

# Implement

Resolve repository-relative paths from the repository root.

Repo wrapper around `ce-work`. This file is the team's contract; the underlying tool may change, this contract does not.

## Dependency check (first, always)

Required skill: `ce-work` (compound-engineering plugin). If it is not in your available skills list: **STOP immediately.** Tell the user:

> Missing skill: `ce-work`. Install or enable the compound-engineering plugin, then re-run this workflow.

Then end the turn. Resume only after the user confirms installation.

## Precondition

A human-approved plan exists in `docs/plans/draft/`. If none exists or approval was not given, stop and route to `/plan`. Move the plan to `docs/plans/active/` and bump its `status` before the first code change.

## Flow

1. **Execute.** Invoke `ce-work` against the plan. Follow it step by step, tests green at each step.
2. **Epilogue — mandatory.**
   1. **Review**: run `/review` over the branch diff.
   2. **Tests green**: `cd backend && pytest`
   3. **Verify in browser**: run the app (`uvicorn app.main:app --reload --port 8000`), test the feature in the browser.
3. **Close out.** Move the plan to `docs/plans/done/`, set `status: done`, fill `## Retro`.
