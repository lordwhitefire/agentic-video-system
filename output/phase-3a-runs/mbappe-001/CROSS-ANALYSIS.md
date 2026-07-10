# Cross-Analysis Report — v3 Script vs v2 Audio vs Clip Durations

**Purpose:** Identify every place where audio duration exceeds available visual duration, so the Planner can fix the v3 script BEFORE the Editor touches it.

---

## V2 Audio Durations (actual TTS output)

| Segment | Words | Duration | WPM |
|---------|-------|----------|-----|
| 1 | 14 | 8.3s | 101 |
| 2 | 118 | 53.0s | 134 |
| 3 | 28 | 11.4s | 148 |
| 4 | 211 | 92.5s | 137 |
| 5 | 308 | 126.7s | 146 |
| 6 | 283 | 128.2s | 132 |
| 7 | 333 | 144.2s | 139 |
| 8 | 135 | 63.7s | 127 |
| 9 | 205 | 79.7s | 154 |
| 10 | 92 | 41.0s | 135 |
| **TOTAL** | **1727** | **748.7s (12:29)** | **138 avg** |

---

## CLIP REUSE ANALYSIS (THE CORE PROBLEM)

The v3 script references clips too many times. Each use needs ~5s of footage, but many clips don't have enough duration to support their reuse count.

| Clip | Available | Times Used | Total Needed (~5s each) | Deficit | Action Required |
|------|-----------|------------|------------------------|---------|-----------------|
| clip-001 | 20.0s | 4 | 20s | 0s | ✅ OK |
| clip-002 | 21.6s | 3 | 15s | 0s | ✅ OK |
| clip-003 | 19.0s | 3 | 15s | 0s | ✅ OK |
| clip-004 | 42.1s | 5 | 25s | 0s | ✅ OK |
| clip-005 | 10.0s | 4 | 20s | **10s** | ⚠️ Reduce to 2 uses |
| clip-006 | 6.0s | 5 | 25s | **19s** | ⚠️ Reduce to 1 use |
| clip-007 | 9.8s | 5 | 25s | **15s** | ⚠️ Reduce to 2 uses |
| clip-008 | 9.0s | 5 | 25s | **16s** | ⚠️ Reduce to 2 uses |
| clip-009 | 16.0s | 4 | 20s | **4s** | Slow down |
| clip-010 | 10.0s | 3 | 15s | **5s** | Slow down |
| clip-011 | 9.0s | 4 | 20s | **11s** | ⚠️ Reduce to 2 uses |
| clip-012 | 13.5s | 3 | 15s | 1.5s | Slow down slightly |
| clip-013 | 14.9s | 3 | 15s | 0.1s | ✅ OK (barely) |
| clip-014 | 10.0s | 3 | 15s | **5s** | Slow down |
| clip-015 | 12.0s | 7 | 35s | **23s** | ⚠️ Reduce to 2-3 uses |
| clip-016 | 6.0s | 3 | 15s | **9s** | ⚠️ Reduce to 1 use |
| clip-017 | 4.7s | 4 | 20s | **15s** | ⚠️ Reduce to 1 use |

### Clips with critical overuse (must fix in v3 script):

1. **clip-015** (France huddle) — used 7 times, only 12s available. Reduce to 2-3 uses.
2. **clip-006** (Mbappé at Madrid, on ground) — used 5 times, only 6s available. Reduce to 1 use.
3. **clip-007** (France team action) — used 5 times, only 9.8s available. Reduce to 2 uses.
4. **clip-008** (France vs Sweden) — used 5 times, only 9s available. Reduce to 2 uses.
5. **clip-017** (World Cup trophy) — used 4 times, only 4.7s available. Reduce to 1 use.
6. **clip-016** (Mbappé France, holding ball) — used 3 times, only 6s available. Reduce to 1 use.
7. **clip-005** (PSG UCL failure) — used 4 times, only 10s available. Reduce to 2 uses.
8. **clip-011** (Bellingham) — used 4 times, only 9s available. Reduce to 2 uses.

### What replaces the reduced clip uses?

Where clips are reduced, the v3 script must replace them with:
- **[GRAPHIC: image+text]** — using our existing images (flexible duration)
- **[ANIMATION: description]** — for tactical concepts (flexible duration)
- **[IMAGE: name]** — still images with Ken Burns effect (flexible duration)
- **[AUTHORITY CLIP: NEEDED]** — if a pundit clip is available

Graphics, animations, and images have **flexible duration** — they can be made as long as the audio needs. This is why they're the safety net.

---

## SEGMENT-BY-SEGMENT DURATION MAP

For each segment, the total audio duration must be filled with visuals. Here's the fill plan:

### Segment 1 — 8.3s
- clip-001 (4s) + clip-002 (4s) = 8s → ✅ FILLED

### Segment 2 — 53.0s
- clip-003 (8s) + clip-004 (8s) + clip-005 (5s) + clip-006 (5s) + GRAPHIC (10s) + clip-003 (8s) + clip-006 (4s) + clip-004 (5s) = 53s
- clip-006 used 2x (10s total, 6s available) → slow down or replace one use with GRAPHIC

### Segment 3 — 11.4s
- clip-004 (5s) + ANIMATION (6s) = 11s → ✅ FILLED

### Segment 4 — 92.5s
- clip-007 (5s) + clip-008 (5s) + GRAPHIC (8s) + GRAPHIC (8s) + GRAPHIC (8s) + clip-015 (5s) + clip-007 (5s) + clip-008 (5s) + IMAGE (8s) + GRAPHIC (8s) + clip-015 (5s) + GRAPHIC (8s) + clip-007 (5s) + GRAPHIC (8s) = 93s
- clip-007 used 3x (15s needed, 9.8s available) → slow down or replace one with IMAGE
- clip-008 used 2x (10s needed, 9s available) → slow down slightly
- clip-015 used 2x (10s needed, 12s available) → ✅ OK

### Segment 5 — 126.7s
- clip-009 (8s) + clip-009 (8s) + AUTHORITY CLIP (15s) + clip-010 (8s) + clip-010 (8s) + GRAPHIC (8s) + clip-011 (8s) + clip-011 (8s) + ANIMATION (8s) + clip-005 (8s) + clip-006 (5s) + GRAPHIC (8s) + GRAPHIC (8s) + GRAPHIC (8s) + GRAPHIC (8s) = 126s
- clip-009 used 2x (16s needed, 16s available) → ✅ OK
- clip-010 used 2x (16s needed, 10s available) → slow down
- clip-011 used 2x (16s needed, 9s available) → slow down
- clip-006 used 1x (5s needed, 6s available) → ✅ OK

### Segment 6 — 128.2s
- clip-012 (8s) + clip-012 (8s) + GRAPHIC (8s) + GRAPHIC (8s) + clip-011 (8s) + ANIMATION (8s) + GRAPHIC (8s) + clip-012 (8s) + GRAPHIC (8s) + clip-007 (8s) + clip-015 (8s) + GRAPHIC (8s) + GRAPHIC (8s) + GRAPHIC (8s) + GRAPHIC (8s) + GRAPHIC (8s) = 128s
- clip-012 used 3x (24s needed, 13.5s available) → slow down or replace 1 use with GRAPHIC
- clip-011 used 1x → ✅ OK
- clip-007 used 1x → ✅ OK
- clip-015 used 1x → ✅ OK

### Segment 7 — 144.2s
- clip-013 (8s) + clip-013 (8s) + clip-009 (8s) + clip-005 (8s) + GRAPHIC (8s) + clip-014 (8s) + clip-014 (8s) + AUTHORITY CLIP (15s) + clip-006 (5s) + GRAPHIC (8s) + GRAPHIC (8s) + clip-015 (8s) + clip-008 (8s) + GRAPHIC (8s) + GRAPHIC (8s) + GRAPHIC (8s) + GRAPHIC (8s) + GRAPHIC (8s) = 145s
- clip-013 used 2x (16s needed, 14.9s available) → slow down slightly
- clip-014 used 2x (16s needed, 10s available) → slow down
- clip-005 used 1x → ✅ OK
- clip-006 used 1x → ✅ OK
- clip-015 used 1x → ✅ OK
- clip-008 used 1x → ✅ OK

### Segment 8 — 63.7s
- clip-015 (8s) + clip-007 (8s) + GRAPHIC (8s) + GRAPHIC (8s) + clip-004 (8s) + clip-001 (8s) + GRAPHIC (8s) + GRAPHIC (8s) = 64s
- clip-015 used 1x → ✅ OK
- clip-007 used 1x → ✅ OK
- clip-004 used 1x → ✅ OK
- clip-001 used 1x → ✅ OK

### Segment 9 — 79.7s
- clip-016 (6s) + clip-017 (5s) + clip-003 (8s) + GRAPHIC (8s) + clip-004 (8s) + GRAPHIC (8s) + clip-008 (8s) + GRAPHIC (8s) + clip-015 (8s) + GRAPHIC (8s) = 83s
- clip-016 used 1x (6s needed, 6s available) → ✅ OK (exact)
- clip-017 used 1x (5s needed, 4.7s available) → slow down slightly
- clip-003 used 1x → ✅ OK
- clip-004 used 1x → ✅ OK
- clip-008 used 1x → ✅ OK
- clip-015 used 1x → ✅ OK

### Segment 10 — 41.0s
- clip-001 (5s) + clip-002 (5s) + GRAPHIC (8s) + GRAPHIC (8s) + clip-017 (4s) + GRAPHIC (8s) = 38s
- clip-001 used 1x → ✅ OK
- clip-002 used 1x → ✅ OK
- clip-017 used 1x (4s needed, 4.7s available) → ✅ OK

---

## METRICS FOR REVIEWER (post-production check)

After the video is produced, the Reviewer checks:

1. **Audio completeness:** Is the full voice track present? (12:29)
2. **Visual completeness:** Every second of audio has a visual (no black frames)
3. **Clip durations:** No clip is shown for longer than its available footage (no blank gaps)
4. **Transition presence:** All [TRANSITION] markers have a visual + audio transition
5. **SFX presence:** All [SFX] markers have the sound effect
6. **Authority clips:** Either present or explicitly skipped (not silently missing)
7. **Graphics:** All [GRAPHIC] markers have image + text (never blank background + text alone)
8. **Animations:** All [ANIMATION] markers have the described animation
9. **Duration match:** Video duration ≈ audio duration (±5%)
10. **No gaps:** blackdetect scan shows zero black frames >0.1s
11. **Clip reuse:** No clip used for more total seconds than it has available
12. **Slow-down compliance:** Any slowed clips are within natural limits (≤1.5x)

---

## WHAT NEEDS TO HAPPEN

1. **Rewrite v3 script** with corrected clip usage (reduce overused clips, replace with GRAPHIC/ANIMATION/IMAGE)
2. **Generate all graphics** (image + text overlays) — Editor creates these with Pillow
3. **Generate all animations** — Editor creates tactical animations with Pillow + ffmpeg
4. **Push all visuals to repo** for user review before video assembly
5. **User approves visuals** → Editor assembles final video with v2 audio
