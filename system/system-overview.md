# System Overview

## Purpose

A **template-driven** video editing system. The user supplies a reference video and a topic. The system analyzes the reference to extract its STRUCTURAL TEMPLATE (segment structure, pacing curve, cutting rhythm, visual vocabulary, audio structure) — NOT its content. The reference's content is discarded. Only the structural shell is preserved.

## The Flow

```
1. ANALYZE      Reference video → Analyzer perceives it → Blueprint (template)
2. PLAN         Blueprint + topic → Planner writes Script + Resource Manifest
3. RESEARCH     Researcher sources clips, images, audio directly
4. EXECUTE      Editor assembles cut from assets + blueprint + script
5. REVIEW       Reviewer scores cut vs Blueprint → pass / revise / branch
6. DELIVER      User reviews, calls corrections, final video delivered
```

## The 8 Agents

| # | Agent | Lane | Phase |
|---|-------|------|-------|
| 01 | Analyzer | Perceive reference → produce Blueprint | Analyze |
| 02 | Planner / Script Writer | Blueprint + topic → Script + Manifest | Plan |
| 03 | Researcher | Source clips, images, audio directly | Plan → Execute |
| 04 | Editor | Asset Bundle + Blueprint + Script → cut | Execute |
| 05 | Reviewer | Cut vs Blueprint → pass / revise / branch | Review |
| 06 | TTS | Script + pacing → voice audio | Execute |
| 07 | Watcher / Blocker | Monitor all agents for inference | Always-on |
| 08 | Investigator | Diagnose blocked agents → report to user | On-demand |

## The 12 Laws

See `laws/` directory. All agents obey all laws. Key laws:
- Law 1: No Inference (the constitution)
- Law 8: Graphics must contain images (never blank background + text)
- Law 9: No image reusing (each graphic uses a different image)
- Law 10: No watermarked images (VLM check after generation)

## Work Tree

- **Root:** the Blueprint (does not branch — it is the spec)
- **Plan-level branches:** discouraged — user picks one before sourcing
- **Execution-level branches:** encouraged, post-sourcing
- **Merge:** not supported — branches are independent, user picks a leaf

## Visual Types

See `system/visual-types.md` for the 5 visual types every video uses.

## Script-Driven Visuals

The script is a COMPLETE PRODUCTION DOCUMENT. Every sentence must be marked with what visual appears on screen:

- `[CLIP: clip-XXX description]` — video clip from asset bundle
- `[GRAPHIC: description]` — designed composition with image + text (NEVER blank background + text)
- `[IMAGE: description]` — still image
- `[ANIMATION: description]` — animated graphic for things that can't be filmed
- `[AUTHORITY CLIP: description]` — pundit/coach speaking (narration PAUSED)
- `[TRANSITION]` — narrative break (story shifts, not every clip change)
- `[SFX: description]` — sound effect

## Audio is the Master

- Audio determines when visuals change
- Visual duration must always be ≥ audio duration
- Silence gaps (natural speech pauses) — visual continues playing
- Authority clips: narration is MUTED, authority clip's own audio plays
- Background music: looped, ducked to 10% under narration

## TTS Engine Hierarchy

| Engine | Role | Voice Cloning | When to Use |
|--------|------|---------------|-------------|
| Coqui XTTS-v2 | Primary (testing) | Yes | Default — CPML license, non-commercial |
| Fish Speech | License upgrade | Yes | Before monetization — MIT-ish license |
| StyleTTS2 | Quality option | Yes | When best quality needed |
| Piper | CPU fallback | **NO** | Only if GPU unavailable — voice changes, requires explicit user approval |
| ElevenLabs | Monetization | Yes (paid) | When monetizing — commercial license |
