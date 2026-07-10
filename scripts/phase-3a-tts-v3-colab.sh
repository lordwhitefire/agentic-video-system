#!/bin/bash
# =============================================================================
# Phase 3a — Coqui TTS Voice Track Generation v3 (Chunked)
# =============================================================================
# Uses voiceover-script-v3-chunked.json which splits long segments into
# chunks under 400 tokens. Chunks are generated separately then stitched
# back into segment audio files.
# =============================================================================

set +e

REPO_DIR="/content/drive/MyDrive/agentic-video-system"
RUN_NAME="mbappe-001"
VOICEOVER_JSON="$REPO_DIR/output/phase-3a-runs/$RUN_NAME/voiceover-script-v3-chunked.json"
OUTPUT_DIR="$REPO_DIR/output/phase-3a-runs/$RUN_NAME/assets/tts"
VOICE_SAMPLE="$REPO_DIR/voice-samples/my-voice-v1.wav"
VENV_PYTHON="/content/coqui-venv/bin/python"

export MPLBACKEND=Agg
export COQUI_TOS_AGREED=1

echo "===================================================="
echo "Phase 3a v3 — TTS Generation (Chunked, <400 tokens)"
echo "===================================================="
echo ""

# Verify
if [ ! -f "$VOICEOVER_JSON" ]; then
    echo "ERROR: $VOICEOVER_JSON not found"
    exit 1
fi
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Coqui venv not found. Run Script 2 first."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

cat > /tmp/generate_tts_v3.py << 'PYEOF'
import json
import os
import subprocess
import time
from pathlib import Path
import torch
from TTS.api import TTS

REPO = Path("/content/drive/MyDrive/agentic-video-system")
JSON_PATH = REPO / "output/phase-3a-runs/mbappe-001/voiceover-script-v3-chunked.json"
OUTPUT_DIR = REPO / "output/phase-3a-runs/mbappe-001/assets/tts"
VOICE_SAMPLE = REPO / "voice-samples/my-voice-v1.wav"

with open(JSON_PATH) as f:
    data = json.load(f)

chunks = data["chunks"]
print(f"Loaded {len(chunks)} chunks, {data['total_words']} words total")
print(f"Max tokens per chunk: {max(c['estimated_tokens'] for c in chunks)}")
print()

# Group chunks by segment
from collections import defaultdict
seg_chunks = defaultdict(list)
for c in chunks:
    seg_chunks[c["segment_id"]].append(c)

print(f"Segments: {len(seg_chunks)}")
for seg_id, seg_cs in seg_chunks.items():
    print(f"  {seg_id}: {len(seg_cs)} chunk(s), {sum(c['word_count'] for c in seg_cs)} words")
print()

# Load model
print("Loading Coqui XTTS-v2...")
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
print(f"Model loaded on {device}")
print()

# Generate each chunk
chunk_files = {}
for i, chunk in enumerate(chunks):
    seg_id = chunk["segment_id"]
    chunk_id = chunk["chunk_id"]
    text = chunk["text"]
    words = chunk["word_count"]

    print(f"Chunk {i+1}/{len(chunks)}: {seg_id} chunk {chunk_id} ({words}w, ~{chunk['estimated_tokens']} tokens)")

    chunk_file = OUTPUT_DIR / f"chunk_{i+1:02d}_{seg_id.replace(' ', '_')}_c{chunk_id}.wav"

    t0 = time.time()
    tts.tts_to_file(
        text=text,
        file_path=str(chunk_file),
        language="en",
        speaker_wav=str(VOICE_SAMPLE)
    )
    elapsed = time.time() - t0

    if chunk_file.exists():
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(chunk_file)],
            capture_output=True, text=True
        )
        dur = float(probe.stdout.strip())
        print(f"  ✅ {chunk_file.name} ({dur:.1f}s, gen {elapsed:.1f}s)")
        chunk_files.setdefault(seg_id, []).append((chunk_id, str(chunk_file), dur))
    else:
        print(f"  ❌ Failed")
    print()

# Stitch chunks back into segments
print("=" * 50)
print("Stitching chunks into segment audio files")
print("=" * 50)
print()

segment_audios = []
seg_idx = 0
for seg_id in sorted(seg_chunks.keys()):
    seg_idx += 1
    chunks_for_seg = chunk_files[seg_id]

    if len(chunks_for_seg) == 1:
        # Single chunk — just use it as the segment audio
        _, file_path, dur = chunks_for_seg[0]
        seg_output = OUTPUT_DIR / f"segment_{seg_idx:02d}.wav"
        subprocess.run(["cp", file_path, str(seg_output)])
        print(f"  Segment {seg_idx} ({seg_id}): single chunk, {dur:.1f}s")
    else:
        # Multiple chunks — concatenate
        concat_list = Path(f"/tmp/seg_{seg_idx}_concat.txt")
        with open(concat_list, 'w') as f:
            for _, file_path, _ in sorted(chunks_for_seg):
                f.write(f"file '{file_path}'\n")

        seg_output = OUTPUT_DIR / f"segment_{seg_idx:02d}.wav"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c", "copy", str(seg_output)
        ], capture_output=True)

        # Get duration
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(seg_output)],
            capture_output=True, text=True
        )
        dur = float(probe.stdout.strip()) if probe.stdout.strip() else 0
        print(f"  Segment {seg_idx} ({seg_id}): {len(chunks_for_seg)} chunks stitched, {dur:.1f}s")

    segment_audios.append({"index": seg_idx, "segment_id": seg_id, "file": str(seg_output), "duration": dur})

# Concatenate all segments into full track
print()
print("Creating full voice track...")
full_concat = Path("/tmp/full_voice_concat.txt")
with open(full_concat, 'w') as f:
    for sa in segment_audios:
        f.write(f"file '{sa['file']}'\n")

full_track = OUTPUT_DIR / "voice-track-full-v3.wav"
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "concat", "-safe", "0", "-i", str(full_concat),
    "-c", "copy", str(full_track)
], capture_output=True)

total_dur = sum(sa["duration"] for sa in segment_audios)
print(f"✅ Full track: {full_track.name} ({total_dur:.1f}s = {int(total_dur//60)}:{int(total_dur%60):02d})")

# Save metadata
metadata = {
    "run_name": "mbappe-001",
    "version": "v3-chunked",
    "engine": "coqui_xtts_v2",
    "device": device,
    "voice_sample": str(VOICE_SAMPLE.relative_to(REPO)),
    "total_segments": len(segment_audios),
    "total_duration_seconds": round(total_dur, 2),
    "total_chunks": len(chunks),
    "max_tokens_per_chunk": max(c["estimated_tokens"] for c in chunks),
    "segments": segment_audios,
    "full_track_file": str(full_track.relative_to(REPO))
}

meta_path = OUTPUT_DIR / "voice-track-v3-metadata.json"
with open(meta_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"✅ Metadata: {meta_path.name}")
print()
print("=" * 50)
print("TTS COMPLETE")
print("=" * 50)
print(f"To commit:")
print(f"  cd {REPO}")
print(f"  git add output/phase-3a-runs/mbappe-001/assets/tts/")
print(f"  git commit -m 'Phase 3a v3: TTS generated (chunked, <400 tokens)'")
print(f"  git push")
PYEOF

$VENV_PYTHON /tmp/generate_tts_v3.py
