# Project Constraints

> Real-world constraints discovered during analysis and throughout the video production pipeline.
> Examples: GPU limits (Colab T4), storage limits (Google Drive), API rate limits, rendering time, file size limits for GitHub.

## Hardware Constraints
- GPU: Google Colab T4 (for TTS and rendering)
- RAM: 4GB minimum (1080p encoding needs more — use Colab)
- Storage: Google Drive (via API, OAuth2)

## Software Constraints
- Coqui XTTS-v2: Python 3.11 only (3.12 incompatible)
- Transformers: pinned >=4.33,<4.41 (BeamSearchScorer removed in 4.50)
- FFmpeg: re-encode concat (not stream copy) to avoid blank frames
- Whisper: word-level timestamps required for audio-as-master sync

## Content Constraints
- No watermarked images (Law 10)
- No reusing images across graphics (Law 9)
- All graphics must contain images (Law 8)
- No face content (current default — faceless only)
- Vertical 1088×1920 (9:16) for TikTok/Shorts format

## Pipeline Constraints
- Audio is MASTER — never split, never rearranged
- Visuals get cut to fit audio, never the other way around
- Every sentence in script must have exactly one primary visual tag
- Authority clips: 10-15 seconds, narration muted, pundit audio plays
