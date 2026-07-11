# Tools Registry

Every tool the system uses, where to get it, and which agent uses it.

## Analysis Tools

| Tool | Repo | Tools Count | Used By | Purpose |
|------|------|-------------|---------|---------|
| faster-whisper | `pip install faster-whisper` | — | Analyzer, TTS | Transcription with word-level timestamps (4x faster than openai-whisper) |
| openai-whisper | `pip install openai-whisper` | — | Analyzer | Full Whisper, more languages, word-level timestamps |
| PySceneDetect | `pip install scenedetect[opencv]` | — | Analyzer | Scene boundary detection (ContentDetector) |
| OpenCV | `pip install opencv-python-headless` | — | Analyzer | Computer vision primitives, object tracking, motion analysis |
| Deep SORT | `github.com/levan92/deep_sort_realtime` | — | Analyzer | Object tracking with appearance descriptors |
| FFmpeg | `apt install ffmpeg` | — | All | Video/audio processing engine (underlies most tools) |

## Editing MCP Servers

| Tool | Repo | Tools Count | Used By | Purpose |
|------|------|-------------|---------|---------|
| mcp-video (KyaniteLabs) | `github.com/KyaniteLabs/mcp-video` | 119 | Editor | Primary editing — trim, merge, effects, overlays, subtitles, scene detection. Has `search_tools` discovery. FFmpeg-based. |
| ffmpeg-mcp (dubnium0) | `github.com/dubnium0/ffmpeg-mcp` | 40+ | Editor | Pure FFmpeg alternative — probe, convert, video, audio, effects, subtitles, streaming |
| kdenlive-mcp-server (Va1bhav512) | `github.com/Va1bhav512/kdenlive-mcp-server` | 36 | Editor | Headless MLT XML control of Kdenlive. 8 categories. Cross-platform. |
| mcp-kdenlive (D-Ogi) | `github.com/D-Ogi/mcp-kdenlive` | — | Editor | Controls live Kdenlive instance via D-Bus (not headless) |
| VFX MCP (conneroisu) | `github.com/conneroisu/vfx-mcp` | — | Editor | FastMCP + ffmpeg-python. Basic/transform/audio/effects modules. **Note: requires Python 3.13+** |
| video-audio-mcp (misbahsy) | `github.com/misbahsy/video-audio-mcp` | ~10+ | Editor | FFmpeg-based — convert, trim, extract_audio, concatenate, add_overlay, remove_silence, add_subtitles |
| studiomeyer-io/mcp-video | — | 8 | Editor | 22 LUT presets (teal-orange, noir, vintage, cyberpunk) + social format export |

## Animation Tools

| Tool | Repo | Tools Count | Used By | Purpose |
|------|------|-------------|---------|---------|
| HyperFrames CLI | `npm install -g hyperframes` | 9 commands | Editor | HTML → video rendering. Deterministic. init, lint, inspect, preview, render, doctor, browser, info, upgrade |
| Remotion | `npm install -g remotion @remotion/cli` | React API | Editor | Code-as-video rendering — spring/interpolate animation, 50+ built-in effects |
| Lottie Creator MCP | Search npm: `lottie-creator-mcp` | Full Creator API | Editor | Vector character rigs / icon-style animation |
| remotion-superpowers | Search npm: `remotion-superpowers` | 5 MCP servers, 13 commands | Editor | Adds TTS, music/SFX gen, stock footage, captions, AI review to Remotion |

## Research Tools

| Tool | Repo | Tools Count | Used By | Purpose |
|------|------|-------------|---------|---------|
| RivalSearchMCP | Search GitHub: `rivalsearch-mcp` | 10 tools, 5 skills, 6 sub-agents | Researcher | OSINT, due diligence, fact-checking. Zero API keys needed. |
| gpt-researcher | `github.com/assafelovic/gpt-researcher` | 5 tools + MCP | Researcher | Planner + execution agents for research. Hybrid web+MCP. |
| Firecrawl MCP | `npm install -g firecrawl-mcp` | 5 tools | Researcher | Raw scraping/search — scrape, map, crawl, search, extract |
| z-ai image-search | `npm install -g z-ai-web-dev-sdk` | 1 command | Researcher | Web image search, returns OSS-hosted URLs |
| z-ai vision | Same SDK | 1 command | Analyzer, Researcher, Reviewer | Vision model for image/frame analysis |

## TTS Engines

| Tool | Install | Used By | Voice Cloning | Hardware | License |
|------|---------|---------|---------------|----------|---------|
| Coqui XTTS-v2 | `pip install TTS==0.22.0` (Python 3.11 venv) | TTS | Yes (6s sample) | GPU | CPML (non-commercial) |
| Fish Speech | `github.com/fishaudio/fish-speech` | TTS | Yes | GPU | MIT-ish |
| StyleTTS2 | `github.com/yl4579/StyleTTS2` | TTS | Yes (voice transfer) | GPU | MIT |
| Piper | `pip install piper-tts` | TTS (fallback) | **NO** | CPU | MIT |
| ElevenLabs | `pip install elevenlabs` | TTS (monetization) | Yes (paid) | API | Commercial |

**Critical:** Coqui requires Python 3.11 (not 3.12). Use `uv venv --python 3.11`. Pin `transformers>=4.33,<4.41` (BeamSearchScorer removed in 4.50). Set `COQUI_TOS_AGREED=1` and `MPLBACKEND=Agg`.

## Infrastructure

| Tool | Repo | Purpose |
|------|------|---------|
| uv | `pip install uv` | Fast Python package manager — installs Python 3.11 for Coqui venv |
| Playwright | `pip install playwright` | Bundled Chromium for Remotion rendering on Colab |
| MCP Python Client | `pip install mcp` | Agent runtime MCP client |
| MCP Node.js SDK | `npm install -g @modelcontextprotocol/sdk` | Node-based MCP server support |

## Intelligence Layer

| Tool | Repo | Tools/Skills | Purpose |
|------|------|-------------|---------|
| OpenMontage | `github.com/calesthio/OpenMontage` | 1039 skills | Pipeline directors, creative techniques, quality checklists, decision matrices |
