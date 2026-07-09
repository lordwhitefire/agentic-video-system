#!/usr/bin/env python3.13
"""
Phase 3a — Analyzer Perception Pass (Local, Memory-Safe)
Continues from where the previous run died. Uses whisper-small to fit in 4GB RAM.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_DIR = Path("/home/z/my-project/repos/agentic-video-system")
RUN_DIR = REPO_DIR / "output" / "phase-3a-runs" / "mbappe-001"
PERCEPTION_DIR = RUN_DIR / "perception"
VIDEO_FULL = Path("/tmp/test-reference-full.mp4")

# Use whisper-small — fits in 4GB RAM
WHISPER_MODEL = "small"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

print("=" * 60)
print(f"Phase 3a — Perception Pass (whisper-small, CPU, int8)")
print("=" * 60)
print()

# -----------------------------------------------------------------------------
# Step 4: faster-whisper transcription (small model, fits in 4GB RAM)
# -----------------------------------------------------------------------------
print(f"[4/7] Running faster-whisper ({WHISPER_MODEL}, CPU, int8)...")
t0 = time.time()

from faster_whisper import WhisperModel

print(f"  Loading model {WHISPER_MODEL} (~480MB)...")
model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)

print(f"  Transcribing (14.4min video, CPU — will take ~5-10 min)...")
segments, info = model.transcribe(str(VIDEO_FULL), beam_size=5)

print(f"  Language: {info.language} (prob: {info.language_probability:.3f})")

transcript_segments = []
full_text_parts = []
seg_count = 0
for seg in segments:
    seg_data = {
        "start": round(seg.start, 2),
        "end": round(seg.end, 2),
        "text": seg.text.strip(),
        "speaker": "speaker_0"
    }
    transcript_segments.append(seg_data)
    full_text_parts.append(seg.text.strip())
    seg_count += 1
    if seg_count % 20 == 0:
        print(f"    ...{seg_count} segments transcribed")

elapsed = time.time() - t0
print(f"  Transcribed {len(transcript_segments)} segments in {elapsed:.1f}s")

transcript_data = {
    "video_path": str(VIDEO_FULL),
    "model": WHISPER_MODEL,
    "device": WHISPER_DEVICE,
    "compute_type": WHISPER_COMPUTE_TYPE,
    "language": info.language,
    "language_probability": round(info.language_probability, 3),
    "duration": round(info.duration, 2),
    "segment_count": len(transcript_segments),
    "transcription_time_seconds": round(elapsed, 1),
    "segments": transcript_segments,
    "full_text": " ".join(full_text_parts)
}

transcript_json = PERCEPTION_DIR / "transcript" / "transcript.json"
transcript_json.write_text(json.dumps(transcript_data, indent=2, ensure_ascii=False))

transcript_txt = PERCEPTION_DIR / "transcript" / "transcript.txt"
with open(transcript_txt, 'w') as f:
    for s in transcript_segments:
        f.write(f"[{s['start']:.2f}s -> {s['end']:.2f}s] {s['text']}\n")

print(f"  ✅ Transcript: {transcript_json}")
print(f"  Total words: {len(' '.join(full_text_parts).split())}")
print("[4/7] Done.\n")

# -----------------------------------------------------------------------------
# Step 5: PySceneDetect scene boundary detection
# -----------------------------------------------------------------------------
print("[5/7] PySceneDetect (ContentDetector, threshold=27)...")
t0 = time.time()

from scenedetect import detect, ContentDetector

scenes = detect(str(VIDEO_FULL), ContentDetector(threshold=27.0))
elapsed = time.time() - t0

scene_list = []
for i, (start, end) in enumerate(scenes):
    start_sec = start.get_seconds()
    end_sec = end.get_seconds()
    scene_list.append({
        "scene_id": i + 1,
        "start": round(start_sec, 2),
        "end": round(end_sec, 2),
        "duration": round(end_sec - start_sec, 2)
    })

durations = [s["duration"] for s in scene_list]
avg_shot = sum(durations) / len(durations) if durations else 0

# Pacing curve — 60s windows
pacing_curve = []
window_size = 60.0
current_window = 0.0
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
if window_shots:
    pacing_curve.append({
        "window_start": round(current_window, 2),
        "window_end": round(current_window + window_size, 2),
        "avg_shot_length": round(sum(window_shots) / len(window_shots), 2),
        "shot_count": len(window_shots)
    })

scenes_data = {
    "video_path": str(VIDEO_FULL),
    "detector": "ContentDetector",
    "threshold": 27.0,
    "detection_time_seconds": round(elapsed, 1),
    "total_scenes": len(scene_list),
    "cut_rhythm": {
        "avg_shot_length": round(avg_shot, 2),
        "min_shot_length": round(min(durations), 2) if durations else 0,
        "max_shot_length": round(max(durations), 2) if durations else 0,
        "total_shots": len(scene_list)
    },
    "pacing_curve": pacing_curve,
    "scenes": scene_list
}

scenes_json = PERCEPTION_DIR / "scenes" / "scenes.json"
scenes_json.write_text(json.dumps(scenes_data, indent=2))

print(f"  ✅ Scenes: {scenes_json}")
print(f"  Total scenes: {len(scene_list)}")
print(f"  Avg shot length: {avg_shot:.2f}s")
print("[5/7] Done.\n")

# -----------------------------------------------------------------------------
# Step 6: Extract frames
# -----------------------------------------------------------------------------
print("[6/7] Extracting frames at shot boundaries + every 30s...")

frames_dir = PERCEPTION_DIR / "frames"
# Get duration from scenes_data
duration = scenes_data["cut_rhythm"]["total_shots"] and scene_list[-1]["end"] or 0
if duration == 0:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(VIDEO_FULL)],
        capture_output=True, text=True
    )
    duration = float(probe.stdout.strip())

timestamps = set()
for scene in scene_list:
    timestamps.add(round(scene["start"], 2))
for t in range(0, int(duration), 30):
    timestamps.add(float(t))
timestamps = sorted(timestamps)

print(f"  Extracting {len(timestamps)} frames...")
extracted = []
for i, ts in enumerate(timestamps):
    frame_path = frames_dir / f"frame_{i:04d}_{ts:.2f}s.jpg"
    result = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-ss", str(ts), "-i", str(VIDEO_FULL),
         "-frames:v", "1", "-q:v", "2", str(frame_path)],
        capture_output=True, text=True
    )
    if result.returncode == 0 and frame_path.exists():
        extracted.append({
            "index": i,
            "timestamp": ts,
            "path": str(frame_path.relative_to(REPO_DIR)),
            "size_kb": round(frame_path.stat().st_size / 1024, 1)
        })

frame_index = {
    "video_path": str(VIDEO_FULL),
    "total_frames": len(extracted),
    "extraction_strategy": "shot_boundaries + 30s intervals",
    "frames": extracted
}
(frames_dir / "frame-index.json").write_text(json.dumps(frame_index, indent=2))
print(f"  ✅ Extracted {len(extracted)} frames")
print("[6/7] Done.\n")

# -----------------------------------------------------------------------------
# Step 7: Audio extraction + waveform + spectrogram
# -----------------------------------------------------------------------------
print("[7/7] Extracting audio + waveform + spectrogram...")

audio_dir = PERCEPTION_DIR / "audio"
audio_wav = audio_dir / "full-audio.wav"

if not audio_wav.exists():
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(VIDEO_FULL),
         "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", str(audio_wav)],
        check=True
    )

waveform_png = audio_dir / "waveform.png"
subprocess.run(
    ["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio_wav),
     "-filter_complex", "showwavespic=s=1920x480:colors=blue",
     "-frames:v", "1", str(waveform_png)],
    check=True
)

spectrogram_png = audio_dir / "spectrogram.png"
subprocess.run(
    ["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio_wav),
     "-lavfi", "showspectrumpic=s=1920x480:legend=1",
     "-frames:v", "1", str(spectrogram_png)],
    check=True
)

audio_summary = {
    "audio_path": str(audio_wav.relative_to(REPO_DIR)),
    "waveform_png": str(waveform_png.relative_to(REPO_DIR)),
    "spectrogram_png": str(spectrogram_png.relative_to(REPO_DIR)),
    "size_mb": round(audio_wav.stat().st_size / 1e6, 2)
}
(audio_dir / "audio-summary.json").write_text(json.dumps(audio_summary, indent=2))

print(f"  ✅ Audio extracted")
print(f"  Waveform: {waveform_png.name}")
print(f"  Spectrogram: {spectrogram_png.name}")
print("[7/7] Done.\n")

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
print("=" * 60)
print("Perception pass complete.")
print("=" * 60)
print()
print(f"Outputs in: {PERCEPTION_DIR}/")
print(f"  transcript/transcript.json  — {len(transcript_segments)} segments")
print(f"  scenes/scenes.json          — {len(scene_list)} scenes")
print(f"  frames/                     — {len(extracted)} frames")
print(f"  audio/                      — audio + waveform + spectrogram")
