# Law 7: No Silent Engine Switching

Switching TTS engines changes the voice. This is forbidden without explicit user approval. If the default engine fails, the agent flags — does not silently fall back.

**Applies to:** TTS agent.
**Example:** If Coqui XTTS-v2 fails, agent does NOT silently switch to Piper (which has no voice cloning). Agent flags and asks user.
**Exception:** User explicitly adds Piper to fallback_chain AND accepts voice change in voice-profile.json.
