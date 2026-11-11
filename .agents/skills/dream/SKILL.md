---
name: dream
description: "Consolidate raw memories into a single context file. Cross-checks facts against the codebase, drops stale ones, dedupes, and compresses. Use when memories have accumulated or context feels stale."
---

# Dream: consolidate raw memories

Goal: turn raw memories under `memory/` into one sharp, verified, compressed `memory/DREAM.md` worth loading into every agent's context.

## Steps

1. **Gather.** Collect every raw memory file under `memory/`.
2. **Verify each fact.** If it names a path, file, function, or env var — confirm it still exists. Classify: verified, stale, or unverifiable.
3. **Handle stale facts.** Mark as stale in the raw file, do not include in DREAM.md. Log the reason.
4. **Consolidate.** Rewrite `memory/DREAM.md` from scratch. Organize by topic, compress hard, tag sources.
5. **Hand off.** Show the diff, do not commit. Human reviews and merges.
