# Structural Review — mbappe-001
## Reviewer Agent: Template Fidelity Check

**Question being answered:** Was the structure extracted incorrectly from the reference (Analyzer error), or did our video fail to match the structure (Editor error)?

---

## Summary Diagnosis

**Root cause: PLANNER wrote a script with insufficient word count.**

The Analyzer extracted the template correctly. The Editor applied the template correctly. The Planner wrote a script that was roughly **half the length** the template required, causing every downstream agent to produce a video that's half the template's duration.

| Agent | Verdict | Notes |
|-------|---------|-------|
| **Analyzer** | ✅ Correct | Blueprint accurately captured segment durations, pacing, visual vocab |
| **Planner** | ❌ Failed | Wrote 1044 words; template required ~1800 words. 6/10 segments too short. |
| **Researcher** | ✅ Correct | Sourced all assets. Fact-checks done. |
| **TTS** | ✅ Correct | Generated audio from the script as written. 7:22 from 1044 words. |
| **Editor** | ✅ Correct | Matched visuals to voice track. Cut rhythm matches template (96.6%). |

---

## Evidence

### 1. Duration Mismatch (Planner Issue)

| Segment | Template | Our Video | Ratio | Verdict |
|---------|----------|-----------|-------|---------|
| cold_open | 8.0s | 13.6s | 169% | ⚠️ TOO LONG |
| hook | 52.0s | 45.3s | 87% | ✅ OK |
| thesis | 14.0s | 9.1s | 65% | ✅ OK |
| act_1 | 106.2s | 48.8s | 46% | ⚠️ TOO SHORT |
| act_2 | 160.4s | 74.5s | 46% | ⚠️ TOO SHORT |
| act_3 | 133.8s | 67.5s | 50% | ⚠️ TOO SHORT |
| act_4 | 166.3s | 66.4s | 40% | ⚠️ TOO SHORT |
| act_5 | 79.3s | 32.8s | 41% | ⚠️ TOO SHORT |
| act_6 | 92.4s | 46.6s | 50% | ⚠️ TOO SHORT |
| conclusion | 50.4s | 37.6s | 75% | ✅ OK |
| **TOTAL** | **862.8s** | **442.3s** | **51%** | |

**Template:** 14:22 (863s)
**Our video:** 7:22 (442s) — **51% of template duration**

### 2. Word Count Mismatch (Planner Issue)

| Metric | Reference | Our Script | Ratio |
|--------|-----------|------------|-------|
| Word count | 1911 | 1044 | 55% |
| WPM | 133 | 142 | 107% |
| Total duration | 14:22 | 7:22 | 51% |

**Speech pace is similar** (133 vs 142 wpm — only 7% difference).
**But total words are 55% of reference** — the Planner simply didn't write enough.

### 3. Cut Rhythm (Editor — Correct)

| Metric | Reference | Our Video | Ratio |
|--------|-----------|-----------|-------|
| Total scenes | 292 | 141 | — |
| Avg shot length | 2.95s | 3.06s | 104% |
| Shots per minute | 20.3 | 19.6 | 96.6% |

**✅ Cut rhythm MATCHES the template.** The Editor correctly matched the reference's fast-cutting style.

### 4. Visual Structure at Proportional Positions (VLM Comparison)

9 frame pairs compared at 10%-90% of each video's duration:

| Position | Reference Frame | Our Frame | Structural Match? |
|----------|----------------|-----------|-------------------|
| 10% | Soccer B-roll | Soccer B-roll | ✅ YES |
| 20% | Close-up B-roll | Close-up B-roll | ✅ YES |
| 30% | Infographic | Infographic | ✅ YES |
| 40% | Analyst explaining | Player on ground | ❌ NO |
| 50% | Player interaction | Split-screen match | ❌ NO |
| 60% | Data visualization | Match + sideline | ❌ NO |
| 70% | Coach on sidelines | Coach on sidelines | ✅ YES |
| 80% | Studio commentary | Text overlay | ✅ YES |
| 90% | Award ceremony | Trophy close-up | ✅ YES |

**Beginning and end match structurally. Middle doesn't** — because the middle segments are compressed (40-50% of template duration), the visual content is out of sync with where it should be proportionally.

---

## Root Cause Analysis

### Why did the Planner write too few words?

The Planner's agent definition (`agents/02-planner-script-writer.md`) instructs it to:
- Map the Blueprint's segment structure onto the user's topic
- Match the pacing — "if the reference's hook is 8 seconds, the new hook should be approximately 8 seconds"
- For every claim, mark `verified` or `needs_research`

**What's missing:** The Planner is not explicitly told to **match word count to segment duration**. It's told to match "pacing" and "segment durations" in general terms, but there's no concrete instruction like:

> "Each segment's word count must produce audio matching the template segment's duration. At ~140 wpm, a 160-second segment requires ~370 words. Write to the word count, not just the topic."

### Why did the Editor produce a correct but short video?

The Editor correctly:
- Matched visuals to the voice track duration (not the template duration)
- Matched the cut rhythm (96.6% of template's shots/min)
- Used the correct visual vocabulary (B-roll + graphics + text)

The Editor cannot make the video longer than the voice track. The voice track is 7:22 because the script is 1044 words. The Editor did its job — it just had less to work with.

### Why did the Analyzer not cause this?

The Analyzer correctly captured:
- 10-segment structure with accurate durations
- Cut rhythm (2.95s avg, 292 shots)
- Visual vocabulary
- Pacing curve

The Blueprint is accurate. The problem is downstream.

---

## The Fix

### Planner Agent Update Needed

Add to `agents/02-planner-script-writer.md`:

```
### Word Count Targeting (CRITICAL)

Each segment's script must produce audio matching the template segment's duration.

Conversion: at ~140 words per minute (standard commentary pace):
- 8 seconds = ~19 words
- 50 seconds = ~117 words
- 100 seconds = ~233 words
- 160 seconds = ~373 words

For each segment, calculate the target word count from the template duration:
  target_words = (template_segment_duration_seconds / 60) * 140

Write to that word count. If you cannot fill the duration with relevant content,
flag it — do NOT shorten the segment. The template's pacing depends on full
segment durations.

DO NOT write "enough to cover the topic." Write ENOUGH TO FILL THE DURATION.
```

### What would change with the fix

If the Planner wrote ~1800 words (matching the reference's 1911):
- Voice track would be ~13 minutes (matching template's 14:22)
- Editor would have 13 minutes of visuals to cut
- Cut rhythm would still be ~20 shots/min
- Total video would be ~13-14 minutes
- Visual structure at proportional positions would match

---

## Verdict

**The structure was extracted correctly (Analyzer ✅).**
**The video did NOT match the structure (Planner ❌).**
**The Editor applied the structure correctly given what it received (Editor ✅).**

The problem is NOT in template extraction. The problem is in template application — specifically, the Planner didn't write enough words to fill the template's segment durations.

Fix the Planner agent's word count targeting, re-generate the script, re-generate TTS, and re-edit. The structural template is sound.
