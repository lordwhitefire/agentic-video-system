# Phase 3a — Manual Runtime Status

**Mode:** Manual — GLM acts as the brain, Colab acts as the hands, GitHub is shared storage.
**Started:** 2026-07-09

## How this works

1. GLM clones the repo at the start of each session.
2. GLM acts as each agent in sequence (Analyzer → Planner → Researcher → Editor → Reviewer → TTS).
3. When a tool needs to run, GLM produces a Colab command. User runs it, pastes output back.
4. GLM produces artifacts (Blueprint, Script, Manifest, etc.) and commits them to this folder.
5. User pulls to see the artifacts.

## Current run

- **Reference video:** test-reference.mp4 (in repo root)
- **Topic:** (pending user input)
- **Status:** Awaiting topic from user. Analyzer can start once topic is confirmed.

## Artifact locations

Artifacts for each run go in `output/phase-3a-runs/{run-name}/`:
- `blueprint.json` — Analyzer's output
- `script.md` — Planner's output
- `manifest.json` — Planner's output (resource manifest)
- `asset-bundle.json` — Researcher's output
- `cut-instructions.md` — Editor's instructions for Colab
- `review-report.json` — Reviewer's output
- `voice-track-instructions.md` — TTS agent's instructions for Colab

## Notes

- This is the manual bootstrap. Phase 3b (autonomous Python runtime) happens later when API keys are available.
- All artifacts are committed to git so they persist across sessions.
- The 8 agent definitions in `agents/` are the spec. GLM reads them and embodies each agent's role.
