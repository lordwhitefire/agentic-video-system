#!/bin/bash
# =============================================================================
# Phase 3a — Coqui TTS Voice Track Generation (Colab)
# Agentic Video Editing System
# =============================================================================
# This script runs on Colab (where Coqui + your cloned voice are already
# installed from Phase 2). It reads the voiceover script from the repo,
# generates audio for each segment with your cloned voice, concatenates
# them into a full voice track, and saves to the repo.
#
# PREREQUISITES:
#   - Phase 2 Script 2 must have been run (Coqui venv exists, voice cloned)
#   - The repo must be on your Google Drive (mounted below)
#   - GPU must be enabled (Runtime → T4 GPU)
#
# How to run on Colab:
#   1. Mount Drive (cell 1)
#   2. Run this script (cell 2):
#      !bash /content/drive/MyDrive/agentic-video-system/scripts/phase-3a-tts-colab.sh
#   3. When done, commit and push the audio
#
# Expected runtime: 10-20 minutes (1044 words on GPU)
# =============================================================================

set +e

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
REPO_DIR="/content/drive/MyDrive/agentic-video-system"
RUN_NAME="mbappe-001"
VOICEOVER_JSON="$REPO_DIR/output/phase-3a-runs/$RUN_NAME/voiceover-script-v2.json"
OUTPUT_DIR="$REPO_DIR/output/phase-3a-runs/$RUN_NAME/assets/tts"
VOICE_SAMPLE="$REPO_DIR/voice-samples/my-voice-v1.wav"

VENV_PYTHON="/content/coqui-venv/bin/python"

# Environment variables (Errors #007, #008)
export MPLBACKEND=Agg
export COQUI_TOS_AGREED=1

echo "===================================================="
echo "Phase 3a — Coqui TTS Voice Track Generation (Colab)"
echo "Run: $RUN_NAME"
echo "===================================================="
echo ""

# -----------------------------------------------------------------------------
# Step 1: Verify prerequisites
# -----------------------------------------------------------------------------
echo "[1/6] Verifying prerequisites..."

if [ ! -f "$VOICEOVER_JSON" ]; then
    echo "ERROR: $VOICEOVER_JSON not found."
    echo "Make sure the repo is on Drive and voiceover-script-v2.json exists."
    exit 1
fi

if [ ! -f "$VOICE_SAMPLE" ]; then
    echo "ERROR: $VOICE_SAMPLE not found."
    echo "Voice sample is needed for cloning."
    exit 1
fi

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Coqui venv not found at $VENV_PYTHON"
    echo "Run Phase 2 Script 2 (colab-02-coqui-xtts-v2.sh) first."
    exit 1
fi

# Verify GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: No GPU detected. Enable GPU: Runtime → Change runtime type → T4 GPU"
    exit 1
fi
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader)
echo "  GPU: $GPU_NAME"
echo "  Coqui venv: $($VENV_PYTHON --version)"
echo "  Voice sample: $(du -h $VOICE_SAMPLE | cut -f1)"
echo "[1/6] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Create output directory
# -----------------------------------------------------------------------------
echo "[2/6] Creating output directory..."
mkdir -p "$OUTPUT_DIR"
echo "  Output: $OUTPUT_DIR"
echo "[2/6] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Generate voice track (Python script via venv)
# -----------------------------------------------------------------------------
echo "[3/6] Generating voice track with Coqui XTTS-v2..."
echo "  (Reading voiceover-script-v2.json, generating per-segment, concatenating)"
echo ""

cat > /tmp/generate_voice_track.py << 'PYEOF'
import json
import os
import sys
import time
import torch
import numpy as np
from pathlib import Path
from TTS.api import TTS

# Paths (from environment)
REPO_DIR = Path("/content/drive/MyDrive/agentic-video-system")
RUN_NAME = "mbappe-001"
VOICEOVER_JSON = REPO_DIR / "output" / "phase-3a-runs" / RUN_NAME / "voiceover-script-v2.json"
OUTPUT_DIR = REPO_DIR / "output" / "phase-3a-runs" / RUN_NAME / "assets" / "tts"
VOICE_SAMPLE = REPO_DIR / "voice-samples" / "my-voice-v1.wav"

# Load voiceover data
with open(VOICEOVER_JSON, 'r') as f:
    data = json.load(f)

segments = data["segments"]
print(f"  Loaded {len(segments)} segments, {data['total_words']} words total")
print(f"  Estimated duration: {data['estimated_total_duration_seconds']}s ({data['estimated_total_duration_seconds']/60:.1f} min)")
print()

# Load Coqui model
print("  Loading Coqui XTTS-v2 model...")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"  Device: {device}")
if device == "cpu":
    print("  WARNING: Running on CPU. Will be slow. Make sure GPU is enabled.")

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
print("  ✅ Model loaded")
print()

# Generate each segment
segment_audios = []
total_duration = 0.0

for i, seg in enumerate(segments):
    seg_id = seg["segment_id"]
    text = seg["text"]
    word_count = seg["word_count"]

    print(f"  Segment {i+1}/{len(segments)}: {seg_id}")
    print(f"    Words: {word_count}")
    print(f"    Text: {text[:80]}...")

    # Generate audio for this segment
    seg_output = OUTPUT_DIR / f"segment_{i+1:02d}_{seg_id.replace(' ', '_').lower()}.wav"

    t0 = time.time()
    tts.tts_to_file(
        text=text,
        file_path=str(seg_output),
        language="en",
        speaker_wav=str(VOICE_SAMPLE)
    )
    elapsed = time.time() - t0

    if seg_output.exists():
        # Get duration
        import subprocess
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(seg_output)],
            capture_output=True, text=True
        )
        duration = float(probe.stdout.strip())
        total_duration += duration
        size_kb = seg_output.stat().st_size / 1024
        print(f"    ✅ Generated: {seg_output.name} ({duration:.1f}s, {size_kb:.0f} KB, gen time {elapsed:.1f}s)")
        segment_audios.append({
            "index": i + 1,
            "segment_id": seg_id,
            "file": str(seg_output.relative_to(REPO_DIR)),
            "duration": round(duration, 2),
            "word_count": word_count,
            "generation_time": round(elapsed, 1)
        })
    else:
        print(f"    ❌ Generation failed for {seg_id}")
    print()

# Concatenate all segments into full voice track
print("  Concatenating segments into full voice track...")

# Create concat list
concat_list = Path("/tmp/voice_concat_list.txt")
with open(concat_list, 'w') as f:
    for seg in segment_audios:
        f.write(f"file '{REPO_DIR / seg['file']}'\n")

full_track = OUTPUT_DIR / "voice-track-full.wav"
subprocess.run(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
     "-i", str(concat_list), "-c", "copy", str(full_track)],
    check=True
)

if full_track.exists():
    full_size_mb = full_track.stat().st_size / 1e6
    print(f"  ✅ Full voice track: {full_track.name}")
    print(f"     Duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"     Size: {full_size_mb:.1f} MB")

# Save metadata
metadata = {
    "run_name": RUN_NAME,
    "engine": "coqui_xtts_v2",
    "device": device,
    "voice_sample": str(VOICE_SAMPLE.relative_to(REPO_DIR)),
    "total_segments": len(segment_audios),
    "total_duration_seconds": round(total_duration, 2),
    "total_duration_formatted": f"{int(total_duration//60)}:{int(total_duration%60):02d}",
    "segments": segment_audios,
    "full_track_file": str(full_track.relative_to(REPO_DIR))
}

metadata_path = OUTPUT_DIR / "voice-track-metadata.json"
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print()
print(f"  ✅ Metadata: {metadata_path.name}")
print()
print("=" * 60)
print("Voice track generation complete!")
print("=" * 60)
print(f"  Full track: {full_track}")
print(f"  Duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
print(f"  Segments: {len(segment_audios)}")
print()
print("Next steps:")
print("  1. Listen to segment_01 to verify the voice sounds like you")
print("  2. If good, commit and push:")
print("     cd /content/drive/MyDrive/agentic-video-system")
print("     git add output/phase-3a-runs/mbappe-001/assets/tts/")
print("     git commit -m 'Phase 3a: Coqui voice track generated'")
print("     git push")
print("  3. Tell GLM the voice track is ready")
PYEOF

$VENV_PYTHON /tmp/generate_voice_track.py
echo ""
echo "[3/6] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 4-6: Summary
# -----------------------------------------------------------------------------
echo "[4/6] Voice track generation complete."
echo "[5/6] Audio files saved to: $OUTPUT_DIR"
echo "[6/6] Ready for commit and push."
echo ""
echo "===================================================="
echo "TTS generation complete."
echo "===================================================="
echo ""
echo "Files generated:"
ls -la "$OUTPUT_DIR/"
echo ""
echo "To commit and push:"
echo "  cd $REPO_DIR"
echo "  git add output/phase-3a-runs/$RUN_NAME/assets/tts/"
echo "  git commit -m 'Phase 3a: Coqui voice track generated'"
echo "  git push"
echo ""
echo "Then tell GLM: 'voice track done'"
