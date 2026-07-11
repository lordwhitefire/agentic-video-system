---
name: script-driven-template-extraction
version: 1.0.0
purpose: >
  Teach the Analyzer agent how to watch a reference video and extract a reusable
  editing template. The template captures HOW the reference was edited — never
  WHAT it was about. The template is later consumed by the Planner to drive
  visual assignment on a new topic.
agent: 01-analyzer
trigger: >
  When the user provides a reference video file (local path or URL) and asks the
  Analyzer to produce a template from it.
output_path: /templates/<reference-name>.json
laws_obeyed:
  - Law 1  (No Inference) — flag any visual type you cannot determine
  - Law 4  (No Carrying Over) — every beat carries exactly one visual type
  - Law 9  (No Image Reusing) — never reproduce the reference's content
  - Law 11 (No Inference About Inference) — every decision rule cites example beats
---

# Skill: Script-Driven Template Extraction

## 0. Who This Skill Is For

You are the **Analyzer**. Your job is to watch one reference video and turn its
editing pattern into a structured template JSON. You are NOT writing a script.
You are NOT sourcing clips. You are NOT making a video. You are extracting a
**pattern** that the Planner will later apply to a brand new topic.

This skill is the entire HOW of your work. Follow it step by step. Do not skip
ahead. Do not improvise.

---

## 1. The Core Principle

> **The script is one. The visuals are many.**
> Anchor on the transcript. Never catalog visuals blind.

A reference video has exactly one narration track (the script). It has many
visuals (a different one for almost every sentence). If you try to catalog the
visuals first — "I see a clip of a stadium, then a graphic of a chart, then a
photo of a player" — you will drown. There is no anchor. Every visual feels
unrelated to the next.

Instead, you start with the transcript. You break it into beats (one beat ≈ one
sentence). Each beat is an anchor point. Then you ask, for each beat: "What did
the editor put on screen while the narrator said THIS?" The pairing is the
pattern. Patterns emerge from the pairing, not from staring at visuals in
isolation.

This is why the skill is called **script-driven** template extraction. The
script drives. The visuals follow.

---

## 2. The 9 Visual Types

Every visual in the reference video falls into exactly ONE of these nine types.
There is no tenth type. If you believe you have found a tenth type, you have
either misclassified one of the nine or you are looking at a transition (which
is not a visual type — it is a way of moving between visual types).

### 2.1 B-roll

**Definition:** Footage of the named subject **doing something but not talking**.
Used to illustrate what the narrator is saying ABOUT the subject.

**Examples:**
- Mbappe training on a pitch (while narrator discusses his work ethic)
- A politician walking into a courthouse (while narrator discusses an indictment)
- A chef plating a dish (while narrator discusses their Michelin stars)

**Distinguishing from Raw Video:** B-roll is always of the SPECIFIC subject the
script is about. Raw Video is generic atmosphere footage (crowd, city skyline,
stock nature) not tied to a named subject.

### 2.2 Image

**Definition:** A still photograph of the specific subject. Frozen, not moving.
May be a portrait, a press photo, a screenshot of a tweet, a newspaper front
page.

**Examples:**
- A headshot of Mbappe in a PSG kit
- A photo of a signed contract on a table
- A screenshot of a tweet from the subject's verified account

**Distinguishing from Static Graphic:** An Image is a PHOTO (captured by a
camera or screenshot of real content). A Static Graphic is GENERATED (text,
charts, shapes — designed, not captured).

### 2.3 Static Graphic

**Definition:** A generated visual that does not move. Text on a colored
background, a chart, a diagram, a labeled map, a comparison table.

**Examples:**
- A title card reading "THE TRANSFER SAGA" over a solid color
- A bar chart comparing Mbappe's stats to other forwards
- A map of Europe with an arrow from Paris to Madrid

**Distinguishing from Animated Graphic:** A Static Graphic is one frame. An
Animated Graphic has motion (bars growing, arrows drawing on, numbers counting
up). If it moves, it is Animated.

### 2.4 Animated Graphic

**Definition:** A generated visual that moves. Charts that build, maps that
pan, text that types on, counters that tick up. Motion is the defining feature.

**Examples:**
- A bar chart where bars grow from zero to their final height over 2 seconds
- A map where a dashed line animates from Paris to Madrid
- A counter that ticks up from $0 to $180M

**Distinguishing from Animation:** An Animated Graphic visualizes DATA or
STRUCTURED INFORMATION (numbers, locations, hierarchies). An Animation
visualizes a NARRATIVE SCENE (a character, a place, a story moment).
Animated Graphic = data in motion. Animation = story in motion.

### 2.5 Animation

**Definition:** A generated narrative visual. Motion graphics that depict a
scene, a character, a story moment — not data. Includes 2D/3D character
animation, illustrated explainer scenes, motion-comic panels.

**Examples:**
- An illustrated animation of Mbappe shaking hands with the Real Madrid
  president (when no real footage of the handshake exists)
- A motion-comic retelling of a historical event
- A 2D character animation walking through a stadium tunnel

**Distinguishing from Animated Graphic:** Animation tells a story; Animated
Graphic shows data. If you removed the labels and numbers and it still made
sense as a scene, it is Animation.

### 2.6 Video Effect

**Definition:** A visual effect applied to footage — color grading shifts,
speed ramps, glitch effects, zoom punches, split screens, kaleidoscope
treatments. Applied ON TOP of another visual type, but tracked separately
because it is an editorial decision.

**Examples:**
- A slow-motion speed ramp on a goal celebration (the underlying visual is
  B-roll; the speed ramp is the Video Effect)
- A glitch transition effect overlaid on a static graphic
- A split-screen showing two players side by side (each side is B-roll; the
  split itself is the Video Effect)

**Important:** Video Effects are recorded as a SECONDARY treatment, not as a
beat's primary visual type. A beat is always B-roll/IMAGE/GRAPHIC/etc. first.
If a Video Effect is present, note it in the beat's `audio_treatment` adjacent
field — but the primary visual type remains the underlying type. Video Effects
also appear as secondary tags in the Planner's tag system.

### 2.7 Authority Clip

**Definition:** A clip of a SPECIFIC PERSON (a pundit, expert, journalist,
the subject themselves) SPEAKING on camera. The defining feature is that we
hear THEIR voice, not the narrator's. The narrator stops, the pundit speaks,
the narrator resumes.

**Examples:**
- A 3-second clip of a sports journalist saying "Mbappe is finished at PSG"
- A 5-second clip of an economist explaining a recession on a news show
- A 2-second clip of the subject themselves in a post-match interview

**Distinguishing from B-roll:** B-roll is the subject NOT talking. Authority
Clip is someone (often NOT the subject) talking ON CAMERA. If you hear a voice
that is not the narrator's and you see the speaker's mouth moving on screen,
it is an Authority Clip.

### 2.8 Transition

**Definition:** The motion/visual bridge BETWEEN two beats. Cuts, dissolves,
whip pans, match cuts, graphic matches, J/L cuts. Transitions are not
themselves visuals — they are the punctuation between visuals.

**Examples:**
- Hard cut from B-roll to a static graphic
- Whip-pan transition between two different b-roll clips
- Cross-dissolve from an image to a video effect

**Important:** Transitions are recorded per-beat as `transition_in` and
`transition_out`. They are NOT a primary visual type. A beat is always one of
the 8 primary types; the transition is how you got in and how you got out.

### 2.9 Raw Video

**Definition:** Generic atmosphere footage NOT tied to a named subject.
Stadium crowds, city skylines, locker rooms (empty), stock nature, generic
"mood" shots. Used as connective tissue or mood-setting.

**Examples:**
- A panning shot of a stadium exterior (no players visible)
- A timelapse of a city skyline at night
- Slow-motion rain falling on an empty pitch

**Distinguishing from B-roll:** B-roll is of the SPECIFIC subject. Raw Video
is generic. If the script is about Mbappe and the visual is a stadium crowd
with no Mbappe in frame, that is Raw Video. If Mbappe is in the frame, it is
B-roll.

### 2.10 Summary Table

| # | Type | Captured or Generated? | Motion? | Primary or Secondary? |
|---|------|------------------------|---------|------------------------|
| 1 | B-roll | Captured (footage) | Yes | Primary |
| 2 | Image | Captured (photo) | No | Primary |
| 3 | Static Graphic | Generated | No | Primary |
| 4 | Animated Graphic | Generated | Yes (data) | Primary |
| 5 | Animation | Generated | Yes (scene) | Primary |
| 6 | Video Effect | Effect on top of footage | Varies | Secondary |
| 7 | Authority Clip | Captured (talking head) | Yes | Primary |
| 8 | Transition | Between beats | Yes | Secondary |
| 9 | Raw Video | Captured (generic) | Yes | Primary |

---

## 3. The 4 Audio Layers

Every reference video has up to four audio layers. Track each one separately.
The template records presence and density, not the actual audio (you do not
reproduce the reference's audio — that would violate Law 9).

### 3.1 Narration

The primary voiceover. The script. This is what becomes the beats. The
Narration layer is ALWAYS present (otherwise there is no script to drive the
template). The Planner will replace this entirely with the new script.

### 3.2 SFX

Sound effects layered under the narration. Whooshes on transitions, impacts on
cuts to graphics, risers on authority clip entrances, ambient textures.

**Recorded as:** `sfx_per_minute` in the rhythm block, and per-beat as `sfx`
(array of SFX descriptions: "whoosh on cut", "riser into authority clip",
"impact on graphic reveal").

### 3.3 Music

Background music bed. May be continuous or stinger-based. May duck under
narration and swell between sentences.

**Recorded as:** presence/absence per beat in the beat's `audio_treatment`
field (e.g., "music bed continuous, ducks under narration, swells into
authority clip"). The Planner will pass a MUSIC secondary tag where the
template shows music presence.

### 3.4 Pundit Audio

The audio of an authority clip — the pundit's actual voice. This is recorded
SEPARATELY from narration because it is a different speaker and a different
editorial decision.

**Recorded as:** presence on the beat (the beat's `audio_treatment` will note
"narration stops, pundit audio in"). The Researcher's manifest has a special
`transcript_of_pundit_audio` fill-in slot for these beats.

---

## 4. The 7-Step Extraction Procedure

Follow these steps in order. Do not skip. Do not reorder. Each step depends on
the previous one.

### Step 1 — Get the transcript (Whisper word-level)

Run Whisper on the reference video with **word-level timestamps**. You need
word-level, not segment-level, because beat boundaries are not always sentence
boundaries — a single sentence may be split across two visuals, or two
sentences may share one visual.

```
Tool: faster-whisper or openai-whisper
Mode: word_timestamps=True
Output: list of {word, start, end} tuples
```

If Whisper fails or produces garbage (heavy accent, music drowning the voice,
non-speech dominant), STOP. Flag the reference as `transcription_failed` and
escalate to the user. Do NOT proceed with a bad transcript — every downstream
step depends on it.

### Step 2 — Segment the transcript into beats

Group Whisper words into beats. A beat is the smallest unit of script that
pairs with exactly one visual. Rules:

- One beat ≈ one sentence (but not always — see below).
- If the editor cut to a new visual mid-sentence, split the sentence into two
  beats at the cut point.
- If the editor held one visual across two sentences, merge those sentences
  into one beat.
- Beat boundaries are determined by VISUAL CUTS, not by punctuation.

For each beat, record:
- `index` (0-based)
- `text` (the verbatim narration for that beat)
- `start_seconds` (Whisper timestamp of the first word)
- `end_seconds` (Whisper timestamp of the last word)

### Step 3 — Pair each beat with its visual

For each beat, look at the frame at the beat's midpoint. Determine which of
the 9 visual types is on screen. Use the definitions in §2.

If you can clearly identify the type → record it as the beat's `visual_type`.

If the visual is ambiguous (could be B-roll or Raw Video, could be Static
Graphic or Animated Graphic) → consult §2's distinguishing rules. If still
ambiguous → **FLAG IT** (Law 1). Set `visual_type: "FLAGGED"` and add a note
in `visual_description` explaining what you saw and why you could not decide.
Do NOT guess. Do NOT pick the closest type. Flag it.

For each beat, also record:
- `visual_description` — one sentence describing what is on screen (e.g.,
  "Mbappe in white Real Madrid kit, scoring against Atletico"). This is for
  the Planner's reference, not for reproduction.
- `audio_treatment` — what is happening in audio (e.g., "narration over music
  bed, no SFX"; or "narration stops, pundit audio begins at 0:14").
- `transition_in` — how the visual entered (e.g., "hard cut", "whip pan",
  "cross dissolve from previous beat").
- `transition_out` — how the visual exited.
- `sfx` — array of SFX descriptions for this beat (e.g.,
  `["whoosh on entry", "impact on text reveal"]`). Empty array if none.

### Step 4 — Extract decision rules

Now look across all the beat pairings. Find the patterns. For each pattern,
write a **decision rule** in this format:

```
WHEN narrator says X → editor reaches for Y
```

Where:
- `X` is a trigger phrase pattern (a category of narration content, not a
  verbatim quote — e.g., "a stat or number", "a name being introduced",
  "a judgment or opinion", "a moment of movement or action").
- `Y` is one of the 9 visual types.

**Every rule MUST cite at least two example beats** (Law 11). Without example
beats, the rule is an inference about the editor's reasoning — and inferences
are forbidden.

A rule structure:

```json
{
  "id": "rule-01",
  "trigger_phrase_pattern": "a stat or number is mentioned",
  "visual_type": "animated_graphic",
  "reasoning": "When the narrator cites a number, the editor builds an animated counter or bar chart that ticks up to the value. This appears 4 times in the reference.",
  "example_beats": [3, 7, 12, 19]
}
```

If you cannot find at least two example beats for a proposed rule, **do not
write the rule**. A rule with one example is a guess.

Aim for 5–15 rules. Fewer than 5 means the reference is too uniform (or you
are missing patterns). More than 15 means you are overfitting (collapsing
patterns into one rule).

### Step 5 — Calculate visual proportion

Count the number of beats assigned to each primary visual type. Divide by the
total beat count. This gives you a proportion per type.

```
b_roll_proportion            = (b_roll_beats / total_beats)
image_proportion             = (image_beats / total_beats)
static_graphic_proportion    = (static_graphic_beats / total_beats)
animated_graphic_proportion  = (animated_graphic_beats / total_beats)
animation_proportion         = (animation_beats / total_beats)
video_effect_proportion      = (video_effect_beats / total_beats)  // usually 0; effects are secondary
authority_clip_proportion    = (authority_clip_beats / total_beats)
raw_video_proportion         = (raw_video_beats / total_beats)
```

**The proportions MUST sum to 1.0** (Law: proportions sum to 1.0). If they do
not, you miscounted. Re-count until they sum to 1.0. Video Effect and
Transition proportions are typically 0 because they are secondary treatments,
not primary types — but if a beat's primary visual IS a video effect (rare),
count it.

Round to 4 decimal places.

### Step 6 — Calculate rhythm

Compute the following from the beat list:

| Metric | Formula |
|--------|---------|
| `total_beats` | len(beats) |
| `avg_beat_seconds` | reference_duration_seconds / total_beats |
| `cuts_per_minute` | (number of beats − 1) / (reference_duration_seconds / 60) |
| `transitions_per_minute` | (number of non-hard-cut transitions) / (reference_duration_seconds / 60) |
| `sfx_per_minute` | (total SFX events across all beats) / (reference_duration_seconds / 60) |
| `authority_clip_every_seconds` | reference_duration_seconds / (number of authority_clip beats) — or `null` if zero authority clips |

Round to 2 decimal places. `cuts_per_minute` uses (beats − 1) because N beats
have N−1 cuts between them.

### Step 7 — Extract authority clip pattern

If the reference contains authority clips (proportion > 0), extract the
pattern:

- **Frequency:** How often does an authority clip appear? Use
  `authority_clip_every_seconds` from Step 6.
- **Trigger:** What kind of narration content triggers an authority clip?
  (Same format as decision rules — but specifically for authority clips.)
- **Duration:** What is the typical authority clip length? Average the
  durations of all authority clip beats.
- **Pundit identity pattern:** Are the clips from one recurring pundit, or
  rotating pundits? (Do NOT name the pundits — that would reproduce content.
  Just note the pattern: "single recurring pundit" or "rotating, ~3 distinct
  voices".)

Record this as the `authority_clip_pattern` block in the template.

If the reference has NO authority clips, set `authority_clip_pattern: null`
and `authority_clip_every_seconds: null`.

---

## 5. Decision Rule Format (Reference)

Every decision rule in the template MUST have these 5 fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier: `rule-01`, `rule-02`, etc. |
| `trigger_phrase_pattern` | string | yes | The narration content category that triggers the visual. Phrased as a pattern, not a quote. |
| `visual_type` | string | yes | One of the 9 visual types (or `video_effect` as secondary). |
| `reasoning` | string | yes | One sentence explaining the editor's logic. References the count of occurrences. |
| `example_beats` | array of int | yes | Array of beat indices that demonstrate this rule. Minimum 2 beats. |

**Trigger phrase pattern examples (good):**
- `"a specific number or stat is mentioned"`
- `"a person's name is introduced for the first time"`
- `"a judgment or opinion is delivered"`
- `"a moment of physical movement or action"`
- `"a comparison between two entities"`
- `"a location change is referenced"`

**Trigger phrase pattern examples (bad — too vague or too specific):**
- `"the narrator says something"` (too vague — matches everything)
- `"the narrator says 'one hundred and eighty million dollars'"` (too specific — verbatim quote, not a pattern)

---

## 6. Output: Template JSON Schema

Write the template JSON to `/templates/<reference-name>.json`. The reference
name is derived from the input file name (strip extension, lowercase,
replace spaces with hyphens).

```json
{
  "reference_name": "string — derived from input filename",
  "reference_duration_seconds": "number — total video duration, 2 decimal places",
  "content_type": "string — one of: commentary, explainer, documentary, news, reaction, other",
  "visual_proportion": {
    "b_roll": "number — 0.0 to 1.0, 4 decimal places",
    "image": "number",
    "static_graphic": "number",
    "animated_graphic": "number",
    "animation": "number",
    "video_effect": "number — usually 0",
    "authority_clip": "number",
    "raw_video": "number"
  },
  "rhythm": {
    "total_beats": "integer",
    "avg_beat_seconds": "number — 2 decimal places",
    "cuts_per_minute": "number — 2 decimal places",
    "transitions_per_minute": "number — 2 decimal places",
    "sfx_per_minute": "number — 2 decimal places",
    "authority_clip_every_seconds": "number or null"
  },
  "authority_clip_pattern": {
    "frequency_seconds": "number — same as rhythm.authority_clip_every_seconds",
    "trigger": "string — trigger phrase pattern for authority clips",
    "typical_duration_seconds": "number — average authority clip beat length",
    "pundit_identity_pattern": "string — 'single_recurring', 'rotating', or 'subject_themselves'"
  },
  "decision_rules": [
    {
      "id": "rule-01",
      "trigger_phrase_pattern": "string",
      "visual_type": "string — one of 9 types",
      "reasoning": "string",
      "example_beats": [0, 0]
    }
  ],
  "beats": [
    {
      "index": 0,
      "text": "string — verbatim narration for this beat",
      "start_seconds": "number",
      "end_seconds": "number",
      "visual_type": "string — one of 9 types, or 'FLAGGED'",
      "visual_description": "string — one sentence describing the on-screen visual",
      "audio_treatment": "string — narration / pundit audio / music bed / SFX presence",
      "transition_in": "string — hard cut / whip pan / cross dissolve / etc.",
      "transition_out": "string",
      "sfx": ["string", "string"]
    }
  ]
}
```

---

## 7. Example Template (Excerpt)

Below is an excerpt of a template extracted from a 92-second commentary video
about a football transfer. Shown: the top-level metadata, one decision rule,
and three beats.

```json
{
  "reference_name": "mbappe-transfer-explainer",
  "reference_duration_seconds": 92.40,
  "content_type": "commentary",
  "visual_proportion": {
    "b_roll": 0.4565,
    "image": 0.1304,
    "static_graphic": 0.0870,
    "animated_graphic": 0.1739,
    "animation": 0.0000,
    "video_effect": 0.0000,
    "authority_clip": 0.1087,
    "raw_video": 0.0435
  },
  "rhythm": {
    "total_beats": 23,
    "avg_beat_seconds": 4.02,
    "cuts_per_minute": 14.72,
    "transitions_per_minute": 3.90,
    "sfx_per_minute": 7.79,
    "authority_clip_every_seconds": 92.40
  },
  "authority_clip_pattern": {
    "frequency_seconds": 92.40,
    "trigger": "a strong opinion or judgment is delivered about the subject",
    "typical_duration_seconds": 3.80,
    "pundit_identity_pattern": "single_recurring"
  },
  "decision_rules": [
    {
      "id": "rule-01",
      "trigger_phrase_pattern": "a specific number or monetary figure is mentioned",
      "visual_type": "animated_graphic",
      "reasoning": "When the narrator cites a number, the editor builds an animated counter that ticks up to the value. Appears 4 times in the reference.",
      "example_beats": [3, 7, 12, 19]
    },
    {
      "id": "rule-02",
      "trigger_phrase_pattern": "a strong opinion or judgment is delivered about the subject",
      "visual_type": "authority_clip",
      "reasoning": "When the narrator delivers a verdict, the editor cuts to a pundit clip that echoes the verdict. Appears 1 time in the reference.",
      "example_beats": [15]
    }
  ],
  "beats": [
    {
      "index": 0,
      "text": "So Mbappe finally did it.",
      "start_seconds": 0.20,
      "end_seconds": 1.80,
      "visual_type": "b_roll",
      "visual_description": "Mbappe in a Real Madrid kit walking out of the tunnel.",
      "audio_treatment": "narration over music bed, no SFX",
      "transition_in": "cold open — no transition",
      "transition_out": "hard cut",
      "sfx": []
    },
    {
      "index": 1,
      "text": "After six years of drama at PSG, he's a Madrid player.",
      "start_seconds": 1.85,
      "end_seconds": 5.40,
      "visual_type": "static_graphic",
      "visual_description": "Title card reading 'TRANSFER COMPLETE' over a navy background.",
      "audio_treatment": "narration continues, music bed swells, whoosh SFX on graphic reveal",
      "transition_in": "hard cut",
      "transition_out": "cross dissolve",
      "sfx": ["whoosh on graphic reveal"]
    },
    {
      "index": 15,
      "text": "And according to one Spanish journalist, this is just the beginning.",
      "start_seconds": 64.10,
      "end_seconds": 67.90,
      "visual_type": "authority_clip",
      "visual_description": "Spanish journalist in a studio, speaking to camera. Narration stops, pundit's voice plays.",
      "audio_treatment": "narration stops at 64.10, pundit audio begins. Music bed ducks. Riser SFX into the cut.",
      "transition_in": "whip pan",
      "transition_out": "hard cut",
      "sfx": ["riser into authority clip"]
    }
  ]
}
```

---

## 8. The 10 Hard Rules

These rules are NON-NEGOTIABLE. Violating any one of them invalidates the
template.

1. **Never catalog visuals first.** Always start with the transcript. Always
   break the transcript into beats before assigning any visual type. If you
   find yourself describing visuals without referencing transcript beats, you
   are doing it wrong. Stop and restart at Step 1.

2. **Every beat has exactly one primary visual type.** Not zero. Not two.
   Exactly one. If a beat seems to have two visuals, you split the beat
   incorrectly — go back to Step 2 and re-segment.

3. **If you cannot determine the visual type, FLAG IT.** (Law 1.) Set
   `visual_type: "FLAGGED"` and explain in `visual_description`. Do not guess.
   Do not pick the closest type. The Planner will see the flag and either
   request clarification or apply the default fallback.

4. **Every decision rule must cite at least two example beats.** (Law 11.)
   A rule with zero or one example is an inference about the editor's
   reasoning. Inferences are forbidden. If you cannot find two examples, the
   rule does not exist.

5. **Visual proportions must sum to exactly 1.0.** If they sum to 0.99 or
   1.01, you miscounted. Re-count until they sum to 1.0. This is a sanity
   check that catches missed beats and double-counted beats.

6. **Never reproduce the reference's content.** (Law 9.) The template captures
   PATTERN, not content. Do not name pundits. Do not quote the script verbatim
   beyond what is needed for beat text. Do not include the reference's actual
   images, audio, or footage in the template. The beat text field is the only
   place the reference's words appear, and it is for the Planner's reference
   only — the Planner does NOT reuse these words.

7. **Do not invent a 10th visual type.** The 9 types in §2 are exhaustive. If
   you believe you have found a new type, re-read §2's distinguishing rules.
   If still stuck, flag the beat — do not invent a new type name.

8. **Do not carry over context from previous references.** (Law 4.) Each
   reference is extracted in isolation. If you analyzed a sports commentary
   yesterday and are analyzing a cooking explainer today, do NOT apply sports
   patterns to the cooking video. Start fresh every time.

9. **If Whisper produces a bad transcript, stop.** Do not proceed with a
   transcript full of gaps or hallucinations. Flag `transcription_failed` and
   escalate to the user. A bad transcript produces a bad template — garbage
   in, garbage out.

10. **The template is immutable once written.** If the Planner or Reviewer
    finds a problem with the template later, they escalate to you. They do
    not edit the template themselves. You re-run the extraction (or fix the
    specific issue) and write a new version. Version history lives in the
    file system — never overwrite without recording the prior version.

---

## 9. Law Compliance

This skill obeys the following laws from the system's law set. Each law is
enforced at a specific point in the procedure.

| Law | Enforcement Point |
|-----|-------------------|
| Law 1 (No Inference) | Step 3 — flag any visual type you cannot determine. Step 4 — never write a decision rule with fewer than 2 example beats. |
| Law 4 (No Carrying Over) | Hard Rule 8 — each reference is extracted in isolation. No carryover of patterns from prior references. |
| Law 9 (No Image Reusing / No Reproduction) | Hard Rule 6 — template captures pattern, not content. No pundit names, no verbatim quotes beyond beat text, no actual media. |
| Law 11 (No Inference About Inference) | Step 4 — every decision rule cites example beats. The rule's reasoning references the COUNT of occurrences, not a guess at the editor's mental state. |

If at any point you find yourself about to violate one of these laws, STOP.
Flag the issue in the template (a `_flags` array at the top level, listing
human-readable flag descriptions) and continue with the parts you CAN do
lawfully. The Planner will see the flags and route them to the user.

---

## 10. Handoff Protocol

When the template JSON is written, emit the following message to the
orchestrator:

```json
{
  "from": "01-analyzer",
  "to": "orchestrator",
  "type": "template_ready",
  "payload": {
    "template_path": "/templates/<reference-name>.json",
    "reference_name": "<reference-name>",
    "reference_duration_seconds": 92.40,
    "total_beats": 23,
    "flagged_beats_count": 0,
    "decision_rules_count": 8,
    "authority_clip_present": true,
    "content_type": "commentary",
    "flags": []
  }
}
```

If any beats were flagged (Law 1), include them in the `flags` array:

```json
"flags": [
  {
    "beat_index": 9,
    "issue": "visual type ambiguous — could be animated_graphic or animation. Visual shows an illustrated character of the subject walking, but the walk cycle is data-driven (chart of steps).",
    "resolution_requested": "user clarification on whether to classify as animated_graphic or animation"
  }
]
```

The orchestrator routes the template to the Planner and routes any flags to
the user for resolution.

---

## 11. End Of Skill

This skill is the entire job of the Analyzer. If you follow it step by step,
you will produce a template that the Planner can use to drive visual
assignment on any new topic. If you skip steps or violate the hard rules, the
template will be wrong, and every video built from it will feel wrong.

When in doubt: anchor on the transcript, flag what you cannot determine, cite
example beats for every rule, and never reproduce content.
