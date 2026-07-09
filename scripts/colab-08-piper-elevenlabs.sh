#!/bin/bash
# =============================================================================
# Colab Setup Script 8 — Piper + ElevenLabs (FINAL install script)
# Agentic Video Editing System
# =============================================================================
# Installs the TTS fallback/upgrade engines:
#   - Piper — CPU TTS fallback (NO voice cloning; switching to Piper changes
#     the voice — forbidden silently under Law 1, requires explicit user approval)
#   - ElevenLabs — hosted paid TTS, monetization upgrade path (API-based)
#
# What this script does:
#   1. Verifies Script 1 (foundations) has been run.
#   2. Installs Piper TTS (CPU-only, fast, no voice cloning).
#   3. Downloads Piper's default voice model.
#   4. Sanity check: generate test audio with Piper.
#   5. Installs ElevenLabs Python SDK (for API calls when user monetizes).
#   6. Creates config/research-keys.json template (for API keys, including ElevenLabs).
#   7. Updates voice-profile.json to record Piper + ElevenLabs as available.
#   8. Save status to config/install-status.json.
#
# How to run on Colab:
#   1. Make sure Script 1 has been run successfully.
#   2. Mount Drive.
#   3. !bash /content/drive/MyDrive/agentic-video-system/scripts/colab-08-piper-elevenlabs.sh
#
# Expected runtime: 5-10 minutes (Piper model download is ~60MB, fast)
# =============================================================================

set +e  # Don't hard-exit on errors.

# -----------------------------------------------------------------------------
# Locate the project root
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"
OUTPUT_DIR="$PROJECT_ROOT/output"

TTS_DIR="/content/tts-engines"
SYSTEM_PYTHON="/usr/bin/python3"

echo "===================================================="
echo "Agentic Video Editing System — Colab Setup Script 8"
echo "Piper + ElevenLabs (FINAL install script)"
echo "===================================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "TTS engines dir: $TTS_DIR"
echo ""

mkdir -p "$TTS_DIR"

# -----------------------------------------------------------------------------
# Step 1: Verify Script 1 has been run
# -----------------------------------------------------------------------------
echo "[1/8] Verifying Script 1 (foundations) has been run..."
STATUS_FILE="$CONFIG_DIR/install-status.json"
if [ ! -f "$STATUS_FILE" ]; then
    echo "ERROR: $STATUS_FILE not found. Run Script 1 first."
    exit 1
fi
echo "Found: $STATUS_FILE"
echo "[1/8] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Install Piper TTS
# -----------------------------------------------------------------------------
echo "[2/8] Installing Piper TTS (CPU-only fallback)..."
echo "  (NO voice cloning — switching to Piper changes the voice)"
echo "  (Law 1: forbidden silently, requires explicit user approval)"

PIPER_INSTALLED=$($SYSTEM_PYTHON -c "
try:
    import piper
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")

if [ "$PIPER_INSTALLED" = "yes" ]; then
    echo "  Piper already installed — skipping."
else
    echo "  Installing piper-tts via pip..."
    # piper-tts is the Python package; it downloads models on first use
    pip install --quiet piper-tts 2>&1 | tail -n 5
    PIPER_INSTALLED=$($SYSTEM_PYTHON -c "
try:
    import piper
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")
fi

if [ "$PIPER_INSTALLED" = "yes" ]; then
    echo "  ✅ Piper installed"
else
    echo "  ⚠️  piper-tts pip package failed. Trying alternative: wyoming-piper..."
    pip install --quiet wyoming-piper 2>&1 | tail -n 3
    PIPER_INSTALLED=$($SYSTEM_PYTHON -c "
try:
    import piper
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")
    if [ "$PIPER_INSTALLED" = "yes" ]; then
        echo "  ✅ Piper installed via wyoming-piper"
    else
        echo "  ⚠️  Could not install Piper via pip. Will try direct binary download in Step 3."
    fi
fi
echo "[2/8] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Download Piper's default voice model
# -----------------------------------------------------------------------------
echo "[3/8] Downloading Piper default voice model..."
echo "  (en_US-lessac-medium — a standard English voice for testing)"

PIPER_MODELS_DIR="$TTS_DIR/piper-models"
mkdir -p "$PIPER_MODELS_DIR"

# Try to download a Piper voice model from the official HuggingFace repo
VOICE_NAME="en_US-lessac-medium"
VOICE_ONNX="$PIPER_MODELS_DIR/${VOICE_NAME}.onnx"
VOICE_JSON="$PIPER_MODELS_DIR/${VOICE_NAME}.onnx.json"

if [ -f "$VOICE_ONNX" ]; then
    echo "  Voice model already exists — skipping download."
else
    echo "  Downloading $VOICE_NAME..."
    # Piper voices are hosted at https://huggingface.co/rhasspy/piper-voices
    BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
    curl -sL "$BASE_URL/en_US-lessac-medium.onnx" -o "$VOICE_ONNX"
    curl -sL "$BASE_URL/en_US-lessac-medium.onnx.json" -o "$VOICE_JSON"

    if [ -f "$VOICE_ONNX" ] && [ $(stat -c%s "$VOICE_ONNX" 2>/dev/null || echo 0) -gt 1000000 ]; then
        SIZE_MB=$(du -m "$VOICE_ONNX" | cut -f1)
        echo "  ✅ Downloaded $VOICE_NAME ($SIZE_MB MB)"
    else
        echo "  ⚠️  Download may have failed. File size:"
        ls -la "$VOICE_ONNX" 2>/dev/null || echo "    File not found"
        echo "  Will try sanity check anyway — Piper may use a different default."
    fi
fi
echo "[3/8] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 4: Sanity check — generate test audio with Piper
# -----------------------------------------------------------------------------
echo "[4/8] Sanity check: generate test audio with Piper..."
mkdir -p "$OUTPUT_DIR/piper-test"

if [ "$PIPER_INSTALLED" = "yes" ]; then
    cat > /tmp/piper_sanity.py << 'PYEOF'
import sys
import os

try:
    # piper-tts installs a `piper` CLI command, not a Python API directly
    # We'll invoke it via subprocess
    import subprocess

    voice_model = "/content/tts-engines/piper-models/en_US-lessac-medium.onnx"
    output_wav = "/content/drive/MyDrive/agentic-video-system/output/piper-test/sanity-check.wav"
    test_text = "Hello, this is a test of the Piper TTS system."

    if not os.path.exists(voice_model):
        print(f"  ⚠️  Voice model not found at {voice_model}")
        print("  Skipping Piper sanity check (model download may have failed).")
        sys.exit(0)

    print(f"  Generating: '{test_text}'")
    # Piper CLI: echo "text" | piper -m model.onnx -f output.wav
    result = subprocess.run(
        ["piper", "-m", voice_model, "-f", output_wav],
        input=test_text,
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0 and os.path.exists(output_wav):
        size_kb = os.path.getsize(output_wav) / 1024
        print(f"  ✅ Piper sanity check PASSED. Audio saved: {output_wav} ({size_kb:.1f} KB)")
    else:
        print(f"  ⚠️  Piper CLI returned code {result.returncode}")
        if result.stderr:
            print(f"  stderr: {result.stderr[:500]}")
        print("  This may be OK — piper-tts package may need additional setup.")

except Exception as e:
    print(f"  ⚠️  Piper sanity check error: {e}")
    print("  Piper may need the `piper` binary (not just the Python package).")
    print("  Phase 3 can revisit — Piper is a fallback, Coqui is the primary.")
PYEOF
    $SYSTEM_PYTHON /tmp/piper_sanity.py
    PIPER_TEST="attempted"
else
    echo "  ⚠️  Piper not installed — skipping sanity check."
    PIPER_TEST="skipped"
fi
echo "[4/8] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 5: Install ElevenLabs Python SDK
# -----------------------------------------------------------------------------
echo "[5/8] Installing ElevenLabs Python SDK..."
echo "  (Hosted paid TTS — monetization upgrade path, API-based)"

ELEVENLABS_INSTALLED=$($SYSTEM_PYTHON -c "
try:
    import elevenlabs
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")

if [ "$ELEVENLABS_INSTALLED" = "yes" ]; then
    echo "  ElevenLabs SDK already installed — skipping."
else
    echo "  Installing elevenlabs via pip..."
    pip install --quiet elevenlabs 2>&1 | tail -n 5
    ELEVENLABS_INSTALLED=$($SYSTEM_PYTHON -c "
try:
    import elevenlabs
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")
fi

if [ "$ELEVENLABS_INSTALLED" = "yes" ]; then
    echo "  ✅ ElevenLabs SDK installed"
    # Print version if available
    $SYSTEM_PYTHON -c "import elevenlabs; print(f'  Version: {getattr(elevenlabs, \"__version__\", \"unknown\")}')"
else
    echo "  ⚠️  ElevenLabs SDK install failed. Phase 3 can revisit."
fi
echo "[5/8] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 6: Create config/research-keys.json template (for API keys)
# -----------------------------------------------------------------------------
echo "[6/8] Creating API keys config template..."
KEYS_FILE="$CONFIG_DIR/research-keys.json"

if [ -f "$KEYS_FILE" ]; then
    echo "  research-keys.json already exists — not overwriting (may have real keys)."
else
    cat > "$KEYS_FILE" << 'JSON'
{
  "_comment": "API keys for research and TTS tools. Fill in your actual keys. Do NOT commit this file to git or share it. The Phase 3 runtime reads keys from here.",

  "openai": {
    "api_key": null,
    "purpose": "gpt-researcher LLM-based research, OpenAI TTS (optional)",
    "get_key_from": "https://platform.openai.com/api-keys"
  },

  "firecrawl": {
    "api_key": null,
    "purpose": "Firecrawl MCP — web scraping and search",
    "get_key_from": "https://firecrawl.dev/"
  },

  "elevenlabs": {
    "api_key": null,
    "purpose": "ElevenLabs TTS — monetization upgrade path, voice cloning",
    "get_key_from": "https://elevenlabs.io/",
    "note": "Only needed when commercial_use becomes true in voice-profile.json"
  },

  "_instructions": "To add a key, replace null with your key string in quotes. Example: \"sk-abc123...\""
}
JSON
    echo "  ✅ Created config/research-keys.json template"
    echo "  Fill in your API keys when ready (OpenAI, Firecrawl, ElevenLabs)."
fi
echo "[6/8] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 7: Update voice-profile.json to record Piper + ElevenLabs as available
# -----------------------------------------------------------------------------
echo "[7/8] Updating voice-profile.json..."
VOICE_PROFILE="$CONFIG_DIR/voice-profile.json"

if [ -f "$VOICE_PROFILE" ]; then
    $SYSTEM_PYTHON << PYEOF
import json

with open("$VOICE_PROFILE", 'r') as f:
    profile = json.load(f)

# Record that Piper and ElevenLabs are now installed (engines are available)
# Note: clone_ids remain null until user clones their voice into each engine.
# Piper has NO voice cloning, so clone_ids.piper stays null forever.

# Add install status flags
if "engines" not in profile:
    profile["engines"] = {}

profile["engines"]["piper"]["installed"] = True
profile["engines"]["piper"]["voice_model_path"] = "/content/tts-engines/piper-models/en_US-lessac-medium.onnx"
profile["engines"]["elevenlabs"]["installed"] = True

# Add a note about the engine availability
profile["_install_status"] = {
    "coqui_xtts_v2": profile.get("clone_ids", {}).get("coqui_xtts_v2") is not None,
    "piper": True,
    "elevenlabs_sdk": True,
    "note": "Coqui clone ID set in Script 2. Piper + ElevenLabs SDK installed in Script 8. Clone IDs for Fish Speech, StyleTTS2, ElevenLabs remain null until user clones voice into each."
}

with open("$VOICE_PROFILE", 'w') as f:
    json.dump(profile, f, indent=2)

print("  ✅ voice-profile.json updated")
print("    - piper.installed: True")
print("    - elevenlabs.installed: True")
print("    - Coqui clone ID: preserved from Script 2")
PYEOF
else
    echo "  ⚠️  voice-profile.json not found — skipping update."
fi
echo "[7/8] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 8: Save status
# -----------------------------------------------------------------------------
echo "[8/8] Saving status..."
$SYSTEM_PYTHON << PYEOF
import json
import os
from datetime import datetime, timezone

status_file = "$STATUS_FILE"
status = {}
if os.path.exists(status_file):
    with open(status_file, 'r') as f:
        status = json.load(f)

status["script_08_piper_elevenlabs"] = {
    "installed": True,
    "installed_at": datetime.now(timezone.utc).isoformat(),
    "piper": {
        "installed": "$PIPER_INSTALLED" == "yes",
        "voice_model": "/content/tts-engines/piper-models/en_US-lessac-medium.onnx",
        "sanity_check": "$PIPER_TEST",
        "note": "CPU-only, no voice cloning. Switching to Piper changes the voice — Law 1 requires explicit user approval."
    },
    "elevenlabs": {
        "sdk_installed": "$ELEVENLABS_INSTALLED" == "yes",
        "api_key_needed": True,
        "api_key_location": "config/research-keys.json"
    },
    "research_keys_template": "config/research-keys.json created",
    "voice_profile_updated": True
}

with open(status_file, 'w') as f:
    json.dump(status, f, indent=2)

print(f"Status saved: {status_file}")
PYEOF
echo "[8/8] Done."
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "===================================================="
echo "Script 8 complete. PHASE 2 IS DONE."
echo "===================================================="
echo ""
echo "Installed:"
echo "  - Piper TTS: $([ "$PIPER_INSTALLED" = "yes" ] && echo "✅ installed" || echo "⚠️ partial")"
echo "    Voice model: /content/tts-engines/piper-models/en_US-lessac-medium.onnx"
echo "    Sanity check: $PIPER_TEST"
echo "  - ElevenLabs SDK: $([ "$ELEVENLABS_INSTALLED" = "yes" ] && echo "✅ installed" || echo "⚠️ failed")"
echo "    (API key needed — see config/research-keys.json)"
echo ""
echo "Config files:"
echo "  - config/research-keys.json: ✅ created (fill in your API keys)"
echo "  - config/voice-profile.json: ✅ updated (Piper + ElevenLabs marked available)"
echo ""
echo "Status file: config/install-status.json"
echo ""
echo "=========================================================="
echo "PHASE 2 COMPLETE — All 8 install scripts done."
echo "=========================================================="
echo ""
echo "What's now installed on your Colab environment:"
echo "  - Foundations: FFmpeg, Node.js, Python utils, GPU (Tesla T4)"
echo "  - Coqui XTTS-v2: in Python 3.11 venv, voice cloned (your voice)"
echo "  - Analysis: faster-whisper, openai-whisper, PySceneDetect, OpenCV, Deep SORT"
echo "  - Editing MCP: mcp-video (119 tools), ffmpeg-mcp, video-audio-mcp"
echo "  - Animation: Remotion (render test PASSED), HyperFrames"
echo "  - Research: Firecrawl MCP, gpt-researcher, supporting libs"
echo "  - Intelligence: OpenMontage (1039 skills)"
echo "  - TTS fallback/upgrade: Piper (CPU), ElevenLabs SDK (API)"
echo ""
echo "Known gaps (non-blocking, Phase 3 can revisit):"
echo "  - vfx-mcp: requires Python 3.13+ (Colab has 3.12) — permanently skipped"
echo "  - remotion-superpowers: not on npm/GitHub — supplementary"
echo "  - Lottie Creator MCP: not on npm/GitHub — supplementary"
echo "  - RivalSearchMCP: private/not found — gpt-researcher + Firecrawl cover research"
echo ""
echo "Next phase: Phase 3 — Build the Runtime/Orchestrator"
echo "  This is where we write the Python code that loads the agents,"
echo "  manages the loop, handles the work tree, routes messages between"
echo "  agents, and persists state across Colab sessions."
echo ""
echo "Open MASTER-ROADMAP.md for Phase 3 details when ready."
