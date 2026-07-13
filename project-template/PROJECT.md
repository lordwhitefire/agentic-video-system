# Project Overview

> This file is the entry point. The active department head reads this first. Keep it high-level. Max 300 lines.

## Project Name
(To be filled by the Strategist when a new video project starts)

## Goal
(One paragraph: what video are we making? What reference video? What topic?)

## Reference Video
(Path to the reference video for template extraction)

## Topic
(The subject of the new video)

## Tech Stack Summary
- **Video Processing:** FFmpeg
- **TTS:** Coqui XTTS-v2 (primary), Piper (fallback)
- **Transcription:** Whisper (word-level timestamps)
- **Visual Effects:** mcp-video, Remotion
- **Storage:** Google Drive (via API)

## Current Status
(Not started / Analyzing / Planning / Audio generated / Sourcing / Building visuals / Assembling / Reviewing / Complete)

## Pipeline Stages
1. **Strategy** — Analyzer extracts template, Planner writes script, Researcher produces manifest
2. **Audio** — TTS generates master audio + timestamps
3. **Sourcing** — Human sources clips/images from resource.md
4. **Production** — Editor delegates to 6 visual agents, assembles final video
5. **Quality** — Reviewer checks, Watcher/Blocker monitors, Investigator diagnoses failures

## Key Constraints
See [constraints.md](constraints.md)

## Developer Preferences
See [preferences.md](preferences.md)

## Errors and Fixes Log
See [errors-and-fixes.md](errors-and-fixes.md)
