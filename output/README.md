# output/

This folder holds generated videos, audio, and intermediate artifacts produced by the system.

## What goes here

- Final video cuts (MP4)
- Intermediate renders (preview MP4s, low-quality drafts)
- Generated audio tracks (WAV, MP3)
- Frame extractions (PNG sequences for analysis)
- Render logs

## Structure (created automatically as the system runs)

```
output/
├── {project-name}/                 ← one folder per video project
│   ├── blueprint.json              ← Analyzer's output
│   ├── script.md                   ← Planner's output
│   ├── manifest.json               ← Planner's output
│   ├── asset-bundle.json           ← Researcher's output
│   ├── voice-track.wav             ← TTS agent's output
│   ├── preview-v1.mp4              ← Editor's first preview
│   ├── preview-v2.mp4              ← after revisions
│   ├── final.mp4                   ← final cut
│   └── review-report.json          ← Reviewer's output
```

Project names will be based on your topic (e.g., `mbappe-2022-world-cup/`).

## Currently empty

This folder is empty until you run the system end-to-end. Scripts that produce output will write here automatically.

## Cleanup

Old project folders can be deleted manually to save Drive space. The system does not auto-delete — that's your call.
