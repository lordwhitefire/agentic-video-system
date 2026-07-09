# Agentic Video Editing System — Overview

## Purpose

A reference-driven video editing system. The user supplies a reference video and a topic. The system analyzes the reference to extract its structure, tells the user what resources to source, the user sources them, the system assembles the final cut, reviews it for fidelity to the reference structure, and delivers it for the user's final corrections.

The system does not source resources itself. The user has eyes, can judge copyright, can judge taste, can judge relevance. The system has judgment for structure, pacing, assembly, and execution — not for procurement.

## The Flow

```
1. ANALYZE
   User provides reference video.
   Analyzer perceives it (scenes, transcription, audio, effects, structure)
   and produces the Blueprint — the structural contract.

2. PLAN + SCRIPT
   User provides topic (e.g., "Mbappé").
   Planner/Script Writer reads the Blueprint + topic,
   drafts the script and the Resource Manifest,
   checks in with the user for approval.

3. RESEARCH + MANIFEST
   Researcher reviews the Manifest, proposes candidate sources
   (clips, images, audio) with descriptions and timestamps,
   negotiates with the user. User sources and returns the Asset Bundle.

4. EXECUTE
   Editor assembles the cut from the Asset Bundle + Blueprint + Script.
   Applies animations (HyperFrames / Remotion / Lottie),
   transitions, video effects, captions.
   TTS generates voice matched to the cut.

5. REVIEW
   Reviewer scores the cut against the Blueprint.
   Pass → deliver. Revise → loop back to Editor. Branch → fork the work tree.

6. CORRECTIONS
   System reports to user. User calls corrections.
   Agents either execute the correction or ask a clarifying question.
   No agent auto-corrects beyond what the user specified.

7. DELIVER
   Final cut handed to user. Work tree leaves preserved for comparison.
```

## The Agents

| # | Agent | Lane | Phase |
|---|---|---|---|
| 01 | Analyzer | Perceive reference → produce Blueprint | Analyze |
| 02 | Planner / Script Writer | Blueprint + topic → Script + Manifest | Plan |
| 03 | Researcher | Manifest → proposed sources → user-sourced Asset Bundle | Plan → Execute seam |
| 04 | Editor | Asset Bundle + Blueprint + Script → cut, animations, effects, captions | Execute |
| 05 | Reviewer | Cut vs Blueprint → pass / revise / branch | Review |
| 06 | TTS | Script + pacing → voice audio matched to cut | Execute |
| 07 | Watcher / Blocker | Monitor all agents for inference → revoke + log + escalate | Always-on |
| 08 | Investigator | Diagnose blocked agents → report to user with remediation | On-demand |

Every agent has access to the full tool/skill inventory. Lanes are encoded in each agent's system prompt — agents do not touch work outside their lane. Coordination is by design, not by manual sequencing.

## Law 1 (No Inference)

The constitution of the system. See `laws/law-1-no-inference.md`. No agent fills a gap by guessing. Every gap becomes a flag, an escalation, and a user decision. Enforced structurally by the Watcher/Blocker + Investigator + Reviewer.

## Work Tree

- **Root:** the Blueprint (does not branch — it is the spec).
- **Plan-level branches:** discouraged. The Planner may produce 2–3 candidate plans, but the user picks one before sourcing — sourcing for multiple plans is wasteful.
- **Execution-level branches:** encouraged, post-sourcing. Editor may fork on caption style, music choice, effect variants. Each leaf is a candidate final cut the user can compare.
- **Materialization:** nodes are not pre-rendered. A node is rendered only when the user or Reviewer requests a preview.
- **Merge:** not supported. Branches are independent. User picks a leaf → that leaf becomes HEAD → old branches are archived, not merged.

## Tool & Skill Inventory (Summary)

### Analysis layer
- Tools: video-analyzer, ai-powered-video-analyzer, PySceneDetect, OpenCV, Deep SORT, Whisper, Twelve Labs (paid), Memories.ai (paid), Volces ARK (paid).
- Skills: bsisduck/video-analyzer-skill, fabriqaai/ffmpeg-analyse-video-skill, video-toolkit (emdashcodes), seek-and-analyze-video (Memories.ai-backed), absolutelyskilled video-analyzer, OpenCV CV skill.

### Editing layer
- Tools: mcp-video (KyaniteLabs, 119 tools), kdenlive-mcp-server (36 tools), dubnium0/ffmpeg-mcp (40+ tools), VFX MCP, video-audio-mcp, reap (hosted), Palmier Pro (macOS), studiomeyer-io/mcp-video (8 tools, 22 LUTs).
- Skills: cli-anything-kdenlive, FFmpeg Color & Chromakey skill.

### Animation layer
- Tools: HyperFrames CLI (9 commands), Remotion, Lottie Creator MCP, remotion-superpowers (5 MCP servers, 13 commands).
- Skills: hyperframes entry/core/keyframes/media, remotion core + sub-rules, LottieFiles motion-design-skill.

### Intelligence / orchestration layer
- OpenMontage (52 tools, 500+ skills) — the dominant skills library. Pipeline directors, creative techniques, quality checklists, decision matrix for Remotion vs HyperFrames.

### Research / sourcing layer
- Tools: RivalSearchMCP (10 tools, 5 skills, 6 sub-agents), gpt-researcher (5 tools + MCP), Firecrawl MCP (5 tools), remotion-superpowers media-finder.

### TTS layer
- To be specified. (TTS agent exists; tool inventory pending.)

## Known Gaps (Surface-Level)

- **Video effects detection:** layered/custom effects cannot be reliably identified by analysis. Analyzer flags "something happening at X timestamp," stops, asks user to describe. Description goes into the Blueprint as-is. Bar is "not that bad," not "exact replica."
- **TTS tool inventory:** not yet specified.
- **Graphics generation tooling:** HTML/CSS graphics pipeline (HyperFrames covers some of this) — full pipeline not yet mapped.
- **Researcher asset-sourcing primitives:** Pexels/TwelveLabs/stock retrieval exists inside remotion-superpowers; broader sourcing tooling may be needed.

Gaps are not blocking. They surface as Law 1 flags during execution and get resolved by user description or tool additions as we encounter them.
