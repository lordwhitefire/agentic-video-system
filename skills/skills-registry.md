# Skills Registry

Every skill library the system uses, where to get it, and what it teaches.

## OpenMontage (1039 skills)
**Repo:** `github.com/calesthio/OpenMontage`

The dominant intelligence layer. Contains pipeline directors, creative techniques, quality checklists, tech knowledge packs, and decision matrices.

### Key Skills (from the 1039):

| Skill | Category | What It Teaches |
|-------|----------|----------------|
| video-edit | Editing | How to edit video, structure timelines, apply transitions, manage tracks |
| video-translate | Translation | Video translation pipelines |
| elevenlabs | TTS | ElevenLabs integration patterns |
| tailwind-design-system | Design | Design system principles for UI/graphics |
| threejs-fundamentals | 3D Graphics | Three.js animation fundamentals |
| playwright-recording | Automation | Browser automation for recording |
| acestep | Audio | Audio step sequencing |
| hyperframes-core | Animation | Composition contract — timing, tracks, determinism |
| hyperframes-keyframes | Animation | Keyframe authoring across GSAP/CSS/Anime.js/WAAPI |
| hyperframes-media | Media | Asset preprocessing — TTS, transcribe, remove-background |
| remotion (core) | Animation | Best practices for interpolate/spring, sequencing, transitions |
| remotion/rules/effects.md | Animation | Which effect API to reach for |
| remotion/rules/transitions.md | Animation | Transition timing patterns |
| remotion/rules/text-animations.md | Animation | Text sizing for video-first layout |
| remotion/rules/video-layout.md | Animation | Video layout composition |
| motion-design-skill (LottieFiles) | Design | Disney's 12 animation principles adapted for UI. Timing/easing tables, choreography |

### Decision Matrices in OpenMontage:
- `skills/core/hyperframes.md` — When to route to Remotion vs HyperFrames
- Governance rules against silent runtime swaps

## MCP Server Skills

| Repo | Skills | What It Teaches |
|------|--------|----------------|
| mcp-video (KyaniteLabs) | 1 agent skill | How to use the 119-tool MCP server |
| cli-anything-kdenlive | 1 skill | Driving Kdenlive/MLT via REPL |
| video-use | 1 skill | Natural language video editing via ffmpeg |
| reap | 1 skill | Cursor/Claude Code/Codex API docs for reap.video (10 hosted tools) |

## Analysis Skills

| Repo | Skills | What It Teaches |
|------|--------|----------------|
| bsisduck/video-analyzer-skill | 1 | ffmpeg/whisper scripts + parallel subagent dispatch (grid/keyframe/audio agents) + synthesis |
| fabriqaai/ffmpeg-analyse-video-skill | 1 | ffprobe → frame extraction → disposable sub-agent vision reads → text synthesis |
| video-toolkit (emdashcodes) | 1 | Whisper + Gemini audio + Shazam music ID + keyframe/scene summarization |
| seek-and-analyze-video (kennyzheng) | 1 | Wraps Memories.ai for persistent, cross-video, queryable memory |
| Video Analyzer (crossaitools) | 1 | ffprobe + scene-boundary extraction + AI vision |
| Video Analysis Skill (mcpmarket) | 1 | Volces ARK API — summarization + timestamped key-node extraction |
| OpenCV Computer Vision Skill | 1 | General CV — object detection, feature matching, camera calibration |
| computer-vision-engineer.md | 1 | Agent-role definition for CV pipeline work |

## FFmpeg Skills

| Repo | Skills | What It Teaches |
|------|--------|----------------|
| FFmpeg Color & Chromakey skill | 1 | Exact filter chains for chroma key, LUT application, color space conversion, teal-and-orange/vintage looks |

## Summary

| Source | Skill Count |
|--------|-------------|
| OpenMontage | 1039 |
| MCP server skills | 4 |
| Analysis skills | 8 |
| FFmpeg skills | 1 |
| **Total** | **1052** |
