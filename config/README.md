# config/

This folder holds configuration and state that persists across Colab sessions.

## What lives here

### voice-profile.json

Your TTS voice profile. Specifies:
- Default TTS engine (Coqui XTTS-v2 during testing)
- Clone IDs per engine (null until you clone your voice into each)
- Fallback chain (which engines to try if the default fails — Piper excluded by default)
- Commercial-use flag (false during testing; triggers Coqui exit when you start monetizing)

The TTS agent reads this file at the start of every TTS run. When you clone your voice into a new engine, the clone ID gets written here.

### install-status.json

Written by each install script. Records what's been installed, versions, GPU status. Future scripts read this to skip already-installed components.

### agent-state/ (created at runtime)

When the system is running, agents persist their working state here so they can resume after a Colab session dies mid-run. Not present until Phase 3 (runtime) is built.

### work-tree/ (created at runtime)

The work tree state — nodes, branches, HEAD pointer. Not present until Phase 3.

## Currently contains

- `voice-profile.json` — initial template (all clone IDs null, Coqui as default, Piper not in fallback chain)
- `install-status.json` — created after Script 1 runs successfully

## Editing

You can edit `voice-profile.json` manually if you want to change the default engine or add an engine to the fallback chain. But the TTS agent will also update it automatically when you clone your voice or authorize an engine switch.

Do NOT edit `install-status.json` manually — let the scripts manage it.
