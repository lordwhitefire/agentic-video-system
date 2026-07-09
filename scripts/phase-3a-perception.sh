#!/bin/bash
# =============================================================================
# Phase 3a — Analyzer Perception Pass
# Agentic Video Editing System
# =============================================================================
# This script runs the Analyzer agent's parallel perception pass on the
# reference video. It is invoked manually by the user on Colab during Phase 3a
# (manual runtime, GLM-as-brain mode).
#
# What this script does:
#   1. Finds the repo on Google Drive.
#   2. Reassembles test-reference1.mp4 + test-reference2.mp4 → test-reference-full.mp4
#      (the reference video was split for GitHub's 50MB limit).
#   3. Runs faster-whisper transcription (Coqui venv Python, GPU).
#   4. Runs PySceneDetect scene boundary detection (system Python).
#   5. Extracts frames at shot boundaries + every 30 seconds.
#   6. Extracts audio waveform + spectrogram for visual analysis.
#   7. Saves all outputs to output/phase-3a-runs/{run-name}/perception/
#   8. Prints a summary.
#
# How to run on Colab:
#   1. Mount Drive: from google.colab import drive; drive.mount('/content/drive')
#   2. !bash /content/drive/MyDrive/agentic-video-system/scripts/phase-3a-perception.sh
#
# Expected runtime: 5-15 minutes (Whisper on 14min video + scene detect + frames)
# =============================================================================

set +e  # Don't hard-exit on errors — perception tools are independent.

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
REPO_DIR="/content/drive/MyDrive/agentic-video-system"
RUN_NAME="mbappe-001"  # Change this for different runs
RUN_DIR="$REPO_DIR/output/phase-3a-runs/$RUN_NAME"
PERCEPTION_DIR="$RUN_DIR/perception"

VIDEO_PART1="$REPO_DIR/test-reference1.mp4"
VIDEO_PART2="$REPO_DIR/test-reference2.mp4"
VIDEO_FULL="/content/test-reference-full.mp4"  # Reassembled — in Colab local storage (faster I/O)

VENV_PYTHON="/content/coqui-venv/bin/python"
SYSTEM_PYTHON="/usr/bin/python3"

# Environment variables for venv (Errors #007, #008)
export MPLBACKEND=Agg
export COQUI_TOS_AGREED=1

echo "===================================================="
echo "Phase 3a — Analyzer Perception Pass"
echo "Run: $RUN_NAME"
echo "===================================================="
echo ""
echo "Repo: $REPO_DIR"
echo "Run dir: $RUN_DIR"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Verify inputs
# -----------------------------------------------------------------------------
echo "[1/7] Verifying inputs..."

if [ ! -f "$VIDEO_PART1" ]; then
    echo "ERROR: $VIDEO_PART1 not found."
    echo "Make sure test-reference1.mp4 is in the repo root."
    exit 1
fi
if [ ! -f "$VIDEO_PART2" ]; then
    echo "ERROR: $VIDEO_PART2 not found."
    echo "Make sure test-reference2.mp4 is in the repo root."
    exit 1
fi

# Verify Coqui venv exists (for faster-whisper)
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Coqui venv not found at $VENV_PYTHON"
    echo "Run Script 2 (colab-02-coqui-xtts-v2.sh) first to create the venv."
    echo "faster-whisper was installed into this venv in Script 3."
    exit 1
fi

echo "  All inputs verified."
echo "[1/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Reassemble the two video parts into one continuous video
# -----------------------------------------------------------------------------
echo "[2/7] Reassembling test-reference1.mp4 + test-reference2.mp4 → test-reference-full.mp4..."

# Create a concat list file
cat > /tmp/concat-list.txt << 'EOF'
file '/content/drive/MyDrive/agentic-video-system/test-reference1.mp4'
file '/content/drive/MyDrive/agentic-video-system/test-reference2.mp4'
EOF

# Use ffmpeg concat demuxer (fast, no re-encoding, works when both files have same codec)
ffmpeg -y -f concat -safe 0 -i /tmp/concat-list.txt -c copy "$VIDEO_FULL" 2>&1 | tail -n 5

if [ ! -f "$VIDEO_FULL" ]; then
    echo "ERROR: Reassembly failed. Trying with re-encode (slower but more reliable)..."
    ffmpeg -y -i "$VIDEO_PART1" -i "$VIDEO_PART2" -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]" -map "[outv]" -map "[outa]" "$VIDEO_FULL" 2>&1 | tail -n 5
fi

if [ -f "$VIDEO_FULL" ]; then
    DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO_FULL" 2>/dev/null)
    SIZE_MB=$(du -m "$VIDEO_FULL" | cut -f1)
    echo "  ✅ Reassembled: $VIDEO_FULL"
    echo "  Duration: ${DURATION}s ($(echo "scale=2; $DURATION/60" | bc) min)"
    echo "  Size: ${SIZE_MB} MB"
else
    echo "ERROR: Could not reassemble video."
    exit 1
fi
echo "[2/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Create output directory structure
# -----------------------------------------------------------------------------
echo "[3/7] Creating output directory structure..."
mkdir -p "$PERCEPTION_DIR/transcript"
mkdir -p "$PERCEPTION_DIR/scenes"
mkdir -p "$PERCEPTION_DIR/frames"
mkdir -p "$PERCEPTION_DIR/audio"
echo "  Created: $PERCEPTION_DIR/{transcript,scenes,frames,audio}"
echo "[3/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 4: Run faster-whisper transcription (Coqui venv Python, GPU)
# -----------------------------------------------------------------------------
echo "[4/7] Running faster-whisper transcription (GPU)..."
echo "  (Using whisper-large-v3 for best accuracy on a 14min commentary video)"
echo "  (First run downloads ~3GB model — be patient)"

cat > /tmp/perception_transcribe.py << 'PYEOF'
import json
import os
import sys

video_path = "/content/test-reference-full.mp4"
output_dir = "/content/drive/MyDrive/agentic-video-system/output/phase-3a-runs/mbappe-001/perception/transcript"

print("  Loading faster-whisper (large-v3)...")
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", device="cuda", compute_type="float16")

print(f"  Transcribing: {video_path}")
print("  (This takes a few minutes for a 14min video on T4 GPU)")
segments, info = model.transcribe(video_path, beam_size=5)

print(f"  Detected language: {info.language} (prob: {info.language_probability:.3f})")
print(f"  Duration: {info.duration:.2f}s")

transcript_segments = []
full_text = []
for seg in segments:
    segment_data = {
        "start": round(seg.start, 2),
        "end": round(seg.end, 2),
        "text": seg.text.strip(),
        "speaker": "speaker_0"  # faster-whisper doesn't do diarization by default
    }
    transcript_segments.append(segment_data)
    full_text.append(seg.text.strip())
    print(f"    [{seg.start:.2f}s -> {seg.end:.2f}s] {seg.text.strip()}")

# Save structured transcript
transcript_data = {
    "video_path": video_path,
    "language": info.language,
    "language_probability": round(info.language_probability, 3),
    "duration": round(info.duration, 2),
    "segment_count": len(transcript_segments),
    "segments": transcript_segments,
    "full_text": " ".join(full_text)
}

output_json = os.path.join(output_dir, "transcript.json")
with open(output_json, 'w') as f:
    json.dump(transcript_data, f, indent=2, ensure_ascii=False)
print(f"\n  ✅ Transcript saved: {output_json}")
print(f"  Segments: {len(transcript_segments)}")
print(f"  Total words: {len(' '.join(full_text).split())}")

# Also save plain text for easy reading
output_txt = os.path.join(output_dir, "transcript.txt")
with open(output_txt, 'w') as f:
    for seg in transcript_segments:
        f.write(f"[{seg['start']:.2f}s -> {seg['end']:.2f}s] {seg['text']}\n")
print(f"  Plain text: {output_txt}")
PYEOF

$VENV_PYTHON /tmp/perception_transcribe.py
echo "[4/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 5: Run PySceneDetect scene boundary detection
# -----------------------------------------------------------------------------
echo "[5/7] Running PySceneDetect scene boundary detection..."
echo "  (ContentDetector with threshold 27 — standard for commentary videos)"

cat > /tmp/perception_scenes.py << 'PYEOF'
import json
import os
from scenedetect import detect, ContentDetector

video_path = "/content/test-reference-full.mp4"
output_dir = "/content/drive/MyDrive/agentic-video-system/output/phase-3a-runs/mbappe-001/perception/scenes"

print(f"  Detecting scenes in: {video_path}")
print("  (ContentDetector looks for visual content changes — cuts, transitions)")

scenes = detect(video_path, ContentDetector(threshold=27.0))

print(f"  Detected {len(scenes)} scenes:")
scene_list = []
for i, (start, end) in enumerate(scenes):
    start_sec = start.get_seconds()
    end_sec = end.get_seconds()
    duration = end_sec - start_sec
    scene_data = {
        "scene_id": i + 1,
        "start": round(start_sec, 2),
        "end": round(end_sec, 2),
        "duration": round(duration, 2)
    }
    scene_list.append(scene_data)
    print(f"    Scene {i+1}: {start_sec:.2f}s -> {end_sec:.2f}s ({duration:.2f}s)")

# Calculate cut rhythm statistics
durations = [s["duration"] for s in scene_list]
avg_shot = sum(durations) / len(durations) if durations else 0
min_shot = min(durations) if durations else 0
max_shot = max(durations) if durations else 0

# Pacing curve — shot length over time (binned to 60s windows)
pacing_curve = []
window_size = 60.0
current_window = 0
window_shots = []
for s in scene_list:
    while s["start"] >= current_window + window_size:
        if window_shots:
            pacing_curve.append({
                "window_start": round(current_window, 2),
                "window_end": round(current_window + window_size, 2),
                "avg_shot_length": round(sum(window_shots) / len(window_shots), 2),
                "shot_count": len(window_shots)
            })
        else:
            pacing_curve.append({
                "window_start": round(current_window, 2),
                "window_end": round(current_window + window_size, 2),
                "avg_shot_length": None,
                "shot_count": 0
            })
        current_window += window_size
        window_shots = []
    window_shots.append(s["duration"])

# Final window
if window_shots:
    pacing_curve.append({
        "window_start": round(current_window, 2),
        "window_end": round(current_window + window_size, 2),
        "avg_shot_length": round(sum(window_shots) / len(window_shots), 2),
        "shot_count": len(window_shots)
    })

scenes_data = {
    "video_path": video_path,
    "detector": "ContentDetector",
    "threshold": 27.0,
    "total_scenes": len(scene_list),
    "cut_rhythm": {
        "avg_shot_length": round(avg_shot, 2),
        "min_shot_length": round(min_shot, 2),
        "max_shot_length": round(max_shot, 2),
        "total_shots": len(scene_list)
    },
    "pacing_curve": pacing_curve,
    "scenes": scene_list
}

output_json = os.path.join(output_dir, "scenes.json")
with open(output_json, 'w') as f:
    json.dump(scenes_data, f, indent=2)
print(f"\n  ✅ Scenes saved: {output_json}")
print(f"  Total scenes: {len(scene_list)}")
print(f"  Avg shot length: {avg_shot:.2f}s")
print(f"  Min/Max: {min_shot:.2f}s / {max_shot:.2f}s")
print(f"  Pacing curve windows: {len(pacing_curve)}")
PYEOF

$SYSTEM_PYTHON /tmp/perception_scenes.py
echo "[5/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 6: Extract frames at shot boundaries + every 30 seconds
# -----------------------------------------------------------------------------
echo "[6/7] Extracting frames at shot boundaries + every 30 seconds..."

cat > /tmp/perception_frames.py << 'PYEOF'
import json
import os
import subprocess

video_path = "/content/test-reference-full.mp4"
frames_dir = "/content/drive/MyDrive/agentic-video-system/output/phase-3a-runs/mbappe-001/perception/frames"
scenes_json = "/content/drive/MyDrive/agentic-video-system/output/phase-3a-runs/mbappe-001/perception/scenes/scenes.json"

# Load scenes to get shot boundary timestamps
with open(scenes_json, 'r') as f:
    scenes_data = json.load(f)

# Collect timestamps to extract:
# 1. First frame of each scene (shot boundaries)
# 2. Every 30 seconds (regular sampling for pacing/structure)
timestamps = set()
for scene in scenes_data["scenes"]:
    timestamps.add(round(scene["start"], 2))

# Add 30-second intervals
duration = scenes_data["scenes"][-1]["end"] if scenes_data["scenes"] else 0
for t in range(0, int(duration), 30):
    timestamps.add(float(t))

timestamps = sorted(timestamps)
print(f"  Extracting {len(timestamps)} frames...")

extracted = []
for i, ts in enumerate(timestamps):
    # Extract frame at this timestamp
    frame_path = os.path.join(frames_dir, f"frame_{i:04d}_{ts:.2f}s.jpg")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", str(ts),
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",  # High quality JPEG
        frame_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and os.path.exists(frame_path):
        size_kb = os.path.getsize(frame_path) / 1024
        extracted.append({"index": i, "timestamp": ts, "path": frame_path, "size_kb": round(size_kb, 1)})
        if i % 20 == 0:
            print(f"    Extracted {i+1}/{len(timestamps)} frames...")
    else:
        print(f"    ⚠️  Failed to extract frame at {ts}s: {result.stderr[:100]}")

# Save frame index
frame_index = {
    "video_path": video_path,
    "total_frames": len(extracted),
    "extraction_strategy": "shot_boundaries + 30s intervals",
    "frames": extracted
}

index_path = os.path.join(frames_dir, "frame-index.json")
with open(index_path, 'w') as f:
    json.dump(frame_index, f, indent=2)

print(f"\n  ✅ Extracted {len(extracted)} frames to: {frames_dir}")
print(f"  Frame index: {index_path}")
PYEOF

$SYSTEM_PYTHON /tmp/perception_frames.py
echo "[6/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 7: Extract audio waveform + spectrogram for visual analysis
# -----------------------------------------------------------------------------
echo "[7/7] Extracting audio waveform + spectrogram..."

cat > /tmp/perception_audio.py << 'PYEOF'
import json
import os
import subprocess

video_path = "/content/test-reference-full.mp4"
audio_dir = "/content/drive/MyDrive/agentic-video-system/output/phase-3a-runs/mbappe-001/perception/audio"

# Extract full audio as WAV for analysis
audio_wav = os.path.join(audio_dir, "full-audio.wav")
print("  Extracting full audio track...")
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-i", video_path,
    "-vn",  # No video
    "-acodec", "pcm_s16le",
    "-ar", "44100",
    "-ac", "2",
    audio_wav
], check=True)

audio_size_mb = os.path.getsize(audio_wav) / (1024 * 1024)
print(f"  ✅ Audio extracted: {audio_wav} ({audio_size_mb:.1f} MB)")

# Generate waveform PNG (visual representation of audio over time)
waveform_png = os.path.join(audio_dir, "waveform.png")
print("  Generating waveform PNG...")
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-i", audio_wav,
    "-filter_complex", "showwavespic=s=1920x480:colors=blue",
    "-frames:v", "1",
    waveform_png
], check=True)
print(f"  ✅ Waveform: {waveform_png}")

# Generate spectrogram PNG (frequency analysis over time)
spectrogram_png = os.path.join(audio_dir, "spectrogram.png")
print("  Generating spectrogram PNG...")
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-i", audio_wav,
    "-lavfi", "showspectrumpic=s=1920x480:legend=1",
    "-frames:v", "1",
    spectrogram_png
], check=True)
print(f"  ✅ Spectrogram: {spectrogram_png}")

# Get audio metadata
probe = subprocess.run([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration:stream=sample_rate,channels,bit_rate",
    "-of", "json",
    audio_wav
], capture_output=True, text=True, check=True)
audio_meta = json.loads(probe.stdout)

audio_summary = {
    "audio_path": audio_wav,
    "waveform_png": waveform_png,
    "spectrogram_png": spectrogram_png,
    "size_mb": round(audio_size_mb, 2),
    "metadata": audio_meta
}

summary_path = os.path.join(audio_dir, "audio-summary.json")
with open(summary_path, 'w') as f:
    json.dump(audio_summary, f, indent=2)
print(f"  Summary: {summary_path}")
PYEOF

$SYSTEM_PYTHON /tmp/perception_audio.py
echo "[7/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "===================================================="
echo "Perception pass complete."
echo "===================================================="
echo ""
echo "Outputs in: $PERCEPTION_DIR/"
echo ""
echo "  transcript/"
echo "    transcript.json  — structured transcript with timestamps"
echo "    transcript.txt   — plain text transcript"
echo ""
echo "  scenes/"
echo "    scenes.json      — scene boundaries + cut rhythm + pacing curve"
echo ""
echo "  frames/"
echo "    frame_XXXX_XX.XXs.jpg — extracted frames (shot boundaries + 30s)"
echo "    frame-index.json — index of all extracted frames"
echo ""
echo "  audio/"
echo "    full-audio.wav   — extracted audio track"
echo "    waveform.png     — visual waveform"
echo "    spectrogram.png  — frequency spectrogram"
echo "    audio-summary.json — audio metadata"
echo ""
echo "Next step:"
echo "  1. Commit these outputs to the repo:"
echo "     cd /content/drive/MyDrive/agentic-video-system"
echo "     git add output/phase-3a-runs/$RUN_NAME/perception/"
echo "     git commit -m 'Phase 3a: perception outputs for $RUN_NAME'"
echo "     git push"
echo ""
echo "  2. Tell GLM the perception pass is complete."
echo "     GLM will pull the repo, read the outputs, do vision reads on frames,"
echo "     and synthesize the Blueprint."
