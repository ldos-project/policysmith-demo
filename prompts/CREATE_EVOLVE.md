# Build an evolution loop

Your task: write a small script that uses an LLM to discover better cache eviction policies, and gets better over iterations.

The idea is simple: ask an LLM for a policy, score it, feed the best ones back as inspiration, and repeat. Hand this doc to the coding assistant of your choice (or implement this yourself).

Expected time to finish this: ~15 minutes.

## What is already available
- `llm.py` — the `LLM` class. `llm.send(msg)` → `{"code", "full_response"}`, where `code` is the last code block in the reply. Each instance keeps its own conversation history, so use a fresh `LLM()` per policy.
- `evaluator.py`:
  - `compile_check(code)` → `(ok, error)` — builds the policy. On failure the error string is the compiler output; feed it back to the LLM to fix.
  - `score(code)` → `{"w106_10pct": float}` — byte hit rate, higher is better.
- `prompts/EVICTION.md`: describing how to write a new policy. Use it as-is or feel free to edit for clarity.
- `initial_program.cpp`: implementation of LRU. Can use this as the seed for round 1 and as a baseline.

A policy is a short C++ snippet.

## The loop
- Seed the population with the LRU program and its score.
- Each round, generate a few new policies. Build each one; on a build failure send the error back and let the LLM retry a couple of times before giving up.
- Score what builds, keep it in the population, and feed the current best policies back into the next prompt as inspiration.
- Print progress as you go, and save the final ranked population to a JSON file.