# voice-samples/

This folder holds your voice sample(s) for TTS voice cloning.

## When this folder gets used

The TTS agent (see `agents/06-tts.md`) will demand a voice sample at runtime when:
- It needs to generate audio, AND
- No clone ID exists yet for the selected engine (Coqui XTTS-v2, Fish Speech, StyleTTS2, or ElevenLabs)

The agent does NOT assume a sample exists. It will demand one with concrete format requirements when it needs one.

## What goes here

When the agent demands a sample, it will tell you the requirements. Generally:

- **Duration:** 6+ seconds (10–30 seconds ideal)
- **Format:** WAV or MP3
- **Content:** clean speech, no background music, no other speakers, single speaker (you only)
- **Recommended:** natural conversational pace, varying intonation

## Filename convention

When you add a sample here, name it descriptively:

```
voice-samples/
├── my-voice-v1.wav              ← your first sample
├── my-voice-v2.wav              ← if you record a better one later
└── my-voice-conversational.wav  ← if you want different styles
```

The TTS agent will pick the latest (or ask you which to use).

## Privacy

This folder contains your voice. Treat it like a password — anyone with this sample can clone your voice with Coqui. Do not share this folder publicly. Google Drive is private by default, but be careful if you ever share the parent folder.

## Currently empty

This folder is empty until the TTS agent demands a sample. You don't need to add anything yet.
