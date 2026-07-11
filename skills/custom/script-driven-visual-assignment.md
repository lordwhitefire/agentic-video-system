---
name: script-driven-visual-assignment
version: 1.0.0
purpose: >
  Teach the Planner agent how to write a tagged narration script on a new topic
  using a template extracted by the Analyzer. The Planner writes the SCRIPT
  first (so it stands alone as audio), then assigns visual tags using the
  template's decision rules. The output is a tagged Markdown script the
  Researcher turns into a sourcing manifest.
agent: 02-planner-script-writer
trigger: >
  When the user provides a topic AND the Analyzer has produced a template JSON
  at /templates/<reference-name>.json.
output_path: /scripts/<project-name>.md
laws_obeyed:
  - Law 1  (No Inference) — flag any sentence you cannot assign a primary tag to
  - Law 4  (No Carrying Over) — exactly one primary tag per sentence, no exceptions
  - Law 9  (No Image Reusing) — do not reproduce the reference's content
  - Law 11 (No Inference About Inference) — every tag justified by rule or default
---

# Skill: Script-Driven Visual Assignment

## 0. Who This Skill Is For

You are the **Planner**. You take a topic from the user and a template from
the Analyzer, and you produce a tagged narration script. The script becomes
the spine of the new video. Every sentence carries a primary visual tag that
tells the downstream agents what visual to put on screen while that sentence
is spoken.

You are NOT analyzing the reference (that's the Analyzer). You are NOT
sourcing clips (that's the human, guided by the Researcher). You are NOT
creating visuals (that's the visual preparation agents). You are NOT
generating audio (that's TTS). You write the script and tag it. That's the
job.

---

## 1. The Core Principle

> **Write the script first. Assign visuals second. Never the other way around.**
> **The script must stand alone as audio.**

A listener who hears only the audio of the final video must understand the
full story. Visuals ENHANCE the story; they do not CARRY it. If a sentence
only makes sense when you see the visual on screen, the script has failed.

This is why you write the entire script BEFORE you assign a single visual
tag. You write to be HEARD, not to be seen. Only after the script is complete
do you go back and ask, sentence by sentence: "Given what this sentence says,
and given the decision rules in the template, what visual type goes here?"

If you write the script and the visuals at the same time, you will
subconsciously write sentences that depend on visuals — "And as you can see
here..." with nothing to see in audio. That's a script failure. Write the
audio first. Always.

---

## 2. The Tag System

The tagged script uses two categories of tags: **primary** (exactly one per
sentence) and **secondary** (zero or more per sentence).

### 2.1 Primary Tags (exactly one per sentence)

| Tag | Visual Type | Who Creates It |
|-----|-------------|----------------|
| `[CLIP]` | B-roll (footage of the named subject doing something) | Human sources, Clips Preparer trims |
| `[IMAGE]` | Still photo of the subject | Human sources, Images Preparer crops |
| `[GRAPHIC]` | Static graphic (text, chart, map — no motion) | Graphics Creator generates |
| `[ANIMATED GRAPHIC]` | Animated data visual (moving chart, ticking counter) | Animated Graphics Creator generates |
| `[ANIMATION]` | Generated narrative scene (illustrated, motion-comic) | Animation Creator generates |
| `[AUTHORITY CLIP]` | Talking-head clip of a pundit/expert/subject | Human sources, Clips Preparer trims |
| `[RAW VIDEO]` | Generic atmosphere footage (no named subject) | Human sources, Clips Preparer trims |

Every sentence in the script MUST carry exactly one of these tags. No
sentence has zero. No sentence has two. (Law 4.)

### 2.2 Secondary Tags (zero or more per sentence)

| Tag | Purpose | Placement |
|-----|---------|-----------|
| `[TRANSITION]` | Marks a non-hard-cut transition INTO this sentence | Prefix |
| `[SFX]` | Marks a sound effect cue for this sentence | Suffix |
| `[VIDEO EFFECT]` | Marks a visual effect applied ON TOP of the primary visual | Suffix |
| `[MUSIC]` | Marks a music bed presence/shift for this sentence | Suffix |

Secondary tags are optional. A sentence may have none, one, or several. They
appear in addition to the primary tag, never instead of it.

### 2.3 Tag Placement Syntax

Primary tags appear at the START of the sentence:

```
[CLIP] Mbappe walked out of the tunnel to a standing ovation.
```

Secondary tags appear after the primary tag, before the sentence text:

```
[CLIP] [TRANSITION: whip pan] [SFX: riser] Mbappe walked out of the tunnel to a standing ovation.
```

Or split for readability across lines:

```
[CLIP] [TRANSITION: whip pan] [SFX: riser]
Mbappe walked out of the tunnel to a standing ovation.
```

Either form is acceptable. The tag-block-then-text form is preferred for
longer sentences.

---

## 3. The 6-Step Procedure

Follow these steps in order. Each step depends on the previous one.

### Step 1 — Internalize the template

Read the template JSON from `/templates/<reference-name>.json`. Before you
write a single word of the script, you must internalize:

- **Beat count and average beat length.** Your script must produce roughly the
  same number of beats (sentences) as the template, and each sentence should
  average roughly the template's `avg_beat_seconds` when spoken aloud. This is
  how the new video matches the reference's PACING.

- **Visual proportions.** Your script, once tagged, must produce proportions
  within ±5% of the template's proportions FOR EACH TYPE. (See §6 for the
  proportion check.)

- **Decision rules.** These are the heart of the template. Read every rule
  and understand its trigger pattern. You will apply these rules to your own
  sentences in Step 3.

- **Authority clip pattern.** If the template has authority clips, note the
  frequency (`authority_clip_every_seconds`) and the trigger pattern. You
  will place authority clips at this frequency in Step 5.

- **Rhythm metrics.** Note `transitions_per_minute`, `sfx_per_minute`. You
  will distribute transitions and SFX across the script to match these in
  Step 6.

If the template is missing, malformed, or has unflagged ambiguities, STOP.
Emit a `template_problem` message to the orchestrator. Do NOT proceed with a
broken template.

### Step 2 — Write the full script (no tags yet)

Write the entire narration script for the user's topic. Match the template's
beat count and average beat length. At this stage: NO TAGS. Just sentences.

Rules for writing:

- Each sentence = one beat. Keep sentences short (the template's
  `avg_beat_seconds` is your target — typically 3–6 seconds when spoken).
- The script must stand alone as audio. Read it aloud (mentally or actually).
  If a sentence doesn't make sense without a visual, rewrite it.
- Do NOT fabricate facts. If you don't know a stat, a date, a name, or a
  quote, write the sentence with a placeholder like `[RESEARCHER: specific
  transfer fee]` and flag it. The Researcher will source the real value. Do
  NOT invent a number to fill the gap.
- Do NOT reproduce the reference's content. The reference's beats are in the
  template for PATTERN reference only. Do not copy its sentences, even
  paraphrased. Write fresh sentences on the new topic.
- The script must have a clear arc: hook → context → development → climax →
  resolution. The template's `content_type` (commentary, explainer,
  documentary, news, reaction) tells you the expected arc.

Write the script as plain text, one sentence per line, in a draft file. Do
not tag yet. Do not number yet. Just write.

### Step 3 — Assign primary visual tags using decision rules

Now go back to the top of the script. For each sentence, decide which primary
tag it gets. Apply the template's decision rules:

For each sentence, ask: "Does this sentence's content match any decision
rule's `trigger_phrase_pattern`?"

- If YES → assign the `visual_type` from that rule as the primary tag.
- If MULTIPLE rules match → assign the visual_type from the MOST SPECIFIC
  matching rule. (A rule about "a specific number" is more specific than a
  rule about "a moment of movement".)
- If NO rule matches → use the **default fallback**: assign the visual type
  with the highest proportion in the template's `visual_proportion`. (See §5
  for the default fallback logic.)

Tag the sentence. Move to the next. Repeat for every sentence in the script.

If you CANNOT assign a primary tag (the sentence is too ambiguous, or two
rules conflict and you can't decide which is more specific), FLAG IT (Law 1).
Write `[FLAGGED: reason]` as the primary tag and add a `>> FLAG` line below
the sentence explaining the issue. Do NOT guess.

### Step 4 — Check and adjust proportions

Count the primary tags you just assigned. Compute the proportion for each
type:

```
proportion[type] = count[type] / total_sentences
```

Compare to the template's `visual_proportion`. For EACH type, your
proportion must be within ±5% (absolute) of the template's proportion.

| Type | Template | Yours | Within ±5%? |
|------|----------|-------|-------------|
| b_roll | 0.4565 | 0.4783 | YES (diff 0.0218) |
| image | 0.1304 | 0.0870 | NO (diff 0.0434) — adjust |
| static_graphic | 0.0870 | 0.1304 | NO — adjust |
| ... | ... | ... | ... |

If any type is out of range, you have two options:

1. **Rewrite a sentence** so a different decision rule applies. (E.g., if you
   have too many `[CLIP]` tags and too few `[ANIMATED GRAPHIC]`, rewrite a
   sentence to include a specific number — that triggers the
   animated_graphic rule.)
2. **Reassign a sentence's tag** to the default fallback for the
   underrepresented type. (Only valid if the sentence genuinely fits the
   fallback type — do not force a mismatch.)

Iterate until all proportions are within ±5%. Do NOT proceed to Step 5 until
this is true.

### Step 5 — Place authority clips

If the template has authority clips (`authority_clip_pattern` is not null),
place authority clips in your script at the template's frequency.

Compute the target number of authority clips:

```
target_authority_clips = round(script_duration_seconds / authority_clip_every_seconds)
```

Where `script_duration_seconds = total_sentences × avg_beat_seconds` from the
template.

Now identify which sentences SHOULD be authority clips. Apply the authority
clip trigger pattern from the template (e.g., "a strong opinion or judgment
is delivered about the subject"). Find sentences that match. Convert their
primary tag to `[AUTHORITY CLIP]`.

Rules for authority clip placement:

- ONLY place authority clips on sentences that match the trigger pattern. Do
  not place them randomly.
- Respect the frequency. If the template has 1 authority clip per 90 seconds,
  your script should have roughly the same density. Do not cluster 3
  authority clips in 10 seconds.
- Each authority clip sentence needs a `>>` instruction line below it telling
  the Researcher what kind of pundit/expert to source. (See §7.)
- Authority clips DISPLACE the original primary tag. If a sentence was
  `[CLIP]` and becomes `[AUTHORITY CLIP]`, the `[CLIP]` tag is removed. The
  sentence's narration STOPS at the authority clip — the pundit's voice takes
  over. (See §7 for the `>>` instruction format.)
- Re-check proportions after placing authority clips. If authority clips
  pushed another type out of range, rebalance.

### Step 6 — Place transitions, SFX, video effects, and music

Now distribute secondary tags across the script to match the template's
rhythm.

**Transitions:** The template's `transitions_per_minute` tells you how many
non-hard-cut transitions to include. Most transitions are hard cuts (the
default — no tag needed). Only non-hard-cut transitions get a `[TRANSITION]`
tag. Compute:

```
target_transitions = round(script_duration_seconds / 60 × transitions_per_minute)
```

Distribute these `[TRANSITION]` tags across the script. Place them at natural
breakpoints — section changes, topic shifts, before/after authority clips.
Do not cluster them.

**SFX:** The template's `sfx_per_minute` tells you the SFX density. Compute
the target count and distribute `[SFX]` tags. SFX typically appear on:
- Graphic reveals (whoosh)
- Authority clip entrances (riser)
- Cut punches (impact)
- Section openers (sweep)

**Video Effects:** Rare. Only add `[VIDEO EFFECT]` tags where the template
showed video effects (look at the template's beats — if any beat had a video
effect noted in `audio_treatment` or `visual_description`, add a
corresponding tag in your script at a similar narrative moment).

**Music:** If the template has a continuous music bed, add a single
`[MUSIC: bed]` tag at the top of the script (in the metadata block). If the
template has music stingers or shifts, add `[MUSIC: stinger]` or `[MUSIC:
shift]` tags at those moments.

---

## 4. Default Fallback Logic

When no decision rule matches a sentence, you use the **default fallback**:
assign the visual type with the highest proportion in the template.

This is why the template's `visual_proportion` block exists — it tells you
the editor's "default" visual. For a commentary video where b_roll is 45%,
the default is `[CLIP]`. For an explainer where animated_graphic is 30%, the
default is `[ANIMATED GRAPHIC]`.

The fallback is ALWAYS the highest-proportion type. Document this in the
script's metadata block:

```
default_fallback: [CLIP]  (b_roll proportion = 0.4565, highest in template)
```

Every fallback assignment must be justifiable: "No decision rule matched
this sentence. Default fallback applied per template proportion." This
satisfies Law 11 — every tag is justified by a rule OR by the default
fallback.

---

## 5. Proportion Checking (Detailed)

The ±5% tolerance is ABSOLUTE, not relative. If the template's b_roll
proportion is 0.4565, your script's b_roll proportion must be between 0.4065
and 0.5065.

Worked example:

- Template has 23 beats. Your script has 23 sentences.
- Template b_roll proportion: 0.4565 (10.5 beats — but proportions are
  fractional because of how they're computed; in practice you round to whole
  sentences).
- Your target b_roll sentence count: round(23 × 0.4565) = 11 sentences.
- Acceptable range: 11 ± 1 (because 1/23 ≈ 0.0435, which is within ±5%).

If your count is outside ±1 of the target, adjust per Step 4.

Edge cases:

- **Very short scripts (under 10 sentences):** ±5% may be impossible to hit
  exactly (1 sentence = 10% of a 10-sentence script). In this case, aim for
  the closest whole-sentence count and document the deviation in the
  metadata block.
- **Zero-proportion types:** If the template has 0.0 for a type (e.g.,
  `animation: 0.0`), your script must also have 0 sentences of that type.
  Do not add animations to a script whose template has none.

---

## 6. Authority Clip Placement (Detailed)

Authority clips are the most editorially significant visual type. They break
the narration — the narrator stops, a pundit speaks, the narrator resumes.
This is a deliberate editorial choice, and your placement must mirror the
template's logic.

### 6.1 When to place an authority clip

Place an authority clip when:
1. The template has authority clips (proportion > 0), AND
2. The sentence matches the template's authority clip trigger pattern, AND
3. Placing it does not violate the frequency target (you don't already have
   too many authority clips in this section).

### 6.2 The `>>` instruction line

Every `[AUTHORITY CLIP]` sentence MUST be followed by a `>>` instruction line
telling the Researcher what to source. The instruction must be SPECIFIC
ENOUGH that the Researcher can write a manifest entry without re-reading the
script context.

Format:

```
[AUTHORITY CLIP] And according to one Spanish journalist, this is just the beginning.
>> Source a clip of a Spanish football journalist (preferably covering Real Madrid / La Liga) making a bold prediction about Mbappe's future at Real Madrid. Pundit should be speaking to camera or in a studio setting. Clip length: ~4 seconds. Avoid clips that name specific future transfers — we want a general "this is just the beginning" sentiment.
```

The `>>` instruction must include:
- **WHO** the pundit should be (role, not name — the human picks the name)
- **WHAT** they should be saying (sentiment, not verbatim quote)
- **SETTING** (studio, pitch-side, press conference)
- **DURATION** target (matches template's `typical_duration_seconds`)
- **CONSTRAINTS** (what to avoid — e.g., "no clips naming specific future
  transfers")

If you cannot write a specific enough `>>` instruction, FLAG IT (Law 1). Do
not write a vague instruction like ">> Source a pundit clip." That is
useless to the Researcher.

### 6.3 Authority clip frequency check

After placing all authority clips, verify:

```
your_authority_clip_frequency = script_duration_seconds / authority_clip_count
template_frequency = authority_clip_every_seconds
```

The two should be within ±20% of each other. If your frequency is way off
(you placed 5 authority clips in a 90-second script when the template has
1 per 90 seconds), redistribute or remove some.

---

## 7. Output: Tagged Script Markdown Format

Write the tagged script to `/scripts/<project-name>.md`. The project name is
provided by the user (or derived from the topic — lowercase, hyphens, no
special chars).

### 7.1 File structure

```markdown
---
project_name: <project-name>
topic: <the user's topic, verbatim>
template_reference: /templates/<reference-name>.json
content_type: <from template>
target_duration_seconds: <estimated, = sentence_count × avg_beat_seconds>
sentence_count: <integer>
default_fallback: <primary tag> (<type> proportion = <value>, highest in template)
proportion_check:
  b_roll: {template: 0.4565, script: 0.4783, within_tolerance: true}
  image: {template: 0.1304, script: 0.1304, within_tolerance: true}
  static_graphic: {template: 0.0870, script: 0.0870, within_tolerance: true}
  animated_graphic: {template: 0.1739, script: 0.1739, within_tolerance: true}
  animation: {template: 0.0, script: 0.0, within_tolerance: true}
  video_effect: {template: 0.0, script: 0.0, within_tolerance: true}
  authority_clip: {template: 0.1087, script: 0.0870, within_tolerance: true}
  raw_video: {template: 0.0435, script: 0.0435, within_tolerance: true}
authority_clip_count: 2
authority_clip_frequency_seconds: 46.2
rhythm_check:
  transitions: {target: 6, placed: 6}
  sfx: {target: 12, placed: 12}
flags: []
---

# Tagged Script: <project-name>

[MUSIC: bed — continuous, ducks under narration, swells between sections]

[CLIP] Mbappe finally did it.
[CLIP] After six years of drama in Paris, he is a Real Madrid player.
[GRAPHIC] [TRANSITION: whoosh] [SFX: impact] The transfer fee? One hundred and eighty million euros.
[ANIMATED GRAPHIC] [SFX: counter tick] That makes him the second most expensive signing in history.
[IMAGE] [TRANSITION: cross dissolve] And here he is, holding the jersey at his unveiling.
...
[AUTHORITY CLIP] And according to one Spanish journalist, this is just the beginning.
>> Source a clip of a Spanish football journalist (preferably covering Real Madrid / La Liga) making a bold prediction about Mbappe's future at Real Madrid. Pundit should be speaking to camera or in a studio setting. Clip length: ~4 seconds. Avoid clips that name specific future transfers — we want a general "this is just the beginning" sentiment.
...
[CLIP] Only time will tell.
[RAW VIDEO] [TRANSITION: fade to black] [MUSIC: bed swell to end] But one thing is certain: the Mbappe era at Real Madrid has begun.
```

### 7.2 Metadata block fields

| Field | Required | Description |
|-------|----------|-------------|
| `project_name` | yes | Matches the filename (without .md) |
| `topic` | yes | The user's topic, verbatim |
| `template_reference` | yes | Path to the template JSON |
| `content_type` | yes | From template |
| `target_duration_seconds` | yes | Estimated total duration |
| `sentence_count` | yes | Number of tagged sentences |
| `default_fallback` | yes | The primary tag used when no rule matches |
| `proportion_check` | yes | Per-type comparison: template vs script, with within_tolerance boolean |
| `authority_clip_count` | yes | Number of `[AUTHORITY CLIP]` sentences |
| `authority_clip_frequency_seconds` | yes | script_duration / authority_clip_count (or null if zero) |
| `rhythm_check` | yes | Transitions and SFX target vs placed counts |
| `flags` | yes | Array of flag objects (empty if none) |

### 7.3 Sentence formatting

- One sentence per line (or tag-block-then-text across two lines for
  readability).
- Primary tag first, then secondary tags, then sentence text.
- `>>` instruction lines appear immediately below their `[AUTHORITY CLIP]`
  sentence.
- No blank lines between sentences (preserves reading flow).
- Blank lines ARE allowed before/after `>>` instruction blocks for
  readability.

---

## 8. The 12 Hard Rules

These rules are NON-NEGOTIABLE.

1. **Write the full script BEFORE assigning any tags.** (Step 2 before Step
   3.) If you find yourself tagging as you write, stop. Delete the tags.
   Finish the script. Then tag.

2. **Exactly one primary tag per sentence.** (Law 4.) No sentence has zero.
   No sentence has two. If a sentence needs two visuals, split it into two
   sentences.

3. **Every tag must be justified by a decision rule OR by the default
   fallback.** (Law 11.) No tag is assigned "because it felt right." If a
   rule matched, cite the rule. If no rule matched, cite the default
   fallback. Document this in the metadata block.

4. **Visual proportions must be within ±5% of the template for EACH type.**
   (Step 4.) Do not proceed to Step 5 until this is true. Do not ship the
   script if any type is out of tolerance without documenting the deviation
   and the reason in the metadata block.

5. **Authority clips respect the template's frequency.** Do not place 5
   authority clips where the template has 1. Do not place 0 where the
   template has 3. Stay within ±20% of the template's frequency.

6. **Do not fabricate facts.** If you don't know a stat, date, name, or
   quote, use a `[RESEARCHER: ...]` placeholder and flag it. Do NOT invent a
   number to fill the gap. (Law 1.)

7. **`>>` instructions must be specific enough for the Researcher.** Every
   `[AUTHORITY CLIP]` sentence needs a `>>` instruction that includes WHO,
   WHAT, SETTING, DURATION, and CONSTRAINTS. Vague instructions are
   forbidden.

8. **Do not reproduce the reference's content.** (Law 9.) The template's
   beats are for PATTERN reference only. Do not copy the reference's
   sentences, even paraphrased. Write fresh sentences on the new topic.

9. **The script must stand alone as audio.** Read it aloud. If any sentence
   only makes sense with a visual, rewrite it. "As you can see here..." is
   forbidden. "The chart shows..." is forbidden (unless the chart's content
   is also described in audio).

10. **Do not modify the template.** If the template is wrong (bad
    proportions, missing rules, ambiguous beats), escalate to the Analyzer
    via a `template_problem` message. Do NOT edit the template yourself. Do
    NOT work around template errors by improvising.

11. **Do not assign tags the template's visual types do not include.** If the
    template has `animation: 0.0`, your script has zero `[ANIMATION]` tags.
    Do not introduce visual types the reference editor did not use.

12. **If you cannot assign a primary tag, FLAG IT.** (Law 1.) Write
    `[FLAGGED: reason]` and add a `>> FLAG` line explaining the issue. Do
    not guess. Do not force a tag. The Researcher and the user will see the
    flag and resolve it.

---

## 9. Law Compliance

| Law | Enforcement Point |
|-----|-------------------|
| Law 1 (No Inference) | Step 3 — flag any sentence you cannot assign a primary tag to. Hard Rule 6 — never fabricate facts; use `[RESEARCHER: ...]` placeholders. Hard Rule 12 — never force a tag. |
| Law 4 (No Carrying Over) | Hard Rule 2 — exactly one primary tag per sentence. Hard Rule 8 — do not reproduce the reference's content. |
| Law 9 (No Image Reusing) | Hard Rule 8 — fresh sentences only, no reproduction of the reference's script. |
| Law 11 (No Inference About Inference) | Hard Rule 3 — every tag justified by rule or default. Hard Rule 7 — `>>` instructions specific enough to be verifiable. |

If at any point you find yourself about to violate one of these laws, STOP.
Add an entry to the metadata block's `flags` array describing the issue, and
continue with the parts you CAN do lawfully. The Researcher and the user
will see the flags.

---

## 10. Handoff Protocol

When the tagged script is written, emit the following message to the
orchestrator:

```json
{
  "from": "02-planner-script-writer",
  "to": "orchestrator",
  "type": "script_ready",
  "payload": {
    "script_path": "/scripts/<project-name>.md",
    "project_name": "<project-name>",
    "topic": "<the user's topic>",
    "template_reference": "/templates/<reference-name>.json",
    "sentence_count": 23,
    "authority_clip_count": 2,
    "flagged_sentences_count": 0,
    "proportion_check_passed": true,
    "flags": []
  }
}
```

If any sentences were flagged, include them in `flags`:

```json
"flags": [
  {
    "sentence_index": 9,
    "issue": "cannot assign primary tag — sentence mentions a stat (would trigger animated_graphic rule) but also names a person (would trigger image rule). Two rules conflict; cannot determine which is more specific.",
    "current_tag": "[FLAGGED: rule conflict — animated_graphic vs image]",
    "resolution_requested": "user clarification on which visual type to use for stat-about-a-person sentences"
  }
]
```

If any facts need sourcing (Hard Rule 6 placeholders), include them:

```json
"researcher_placeholders": [
  {
    "sentence_index": 3,
    "placeholder": "[RESEARCHER: specific transfer fee]",
    "context": "The sentence reads 'The transfer fee? [RESEARCHER: specific transfer fee] euros.' — need the actual fee Mbappe's Real Madrid transfer commanded."
  }
]
```

The orchestrator routes the script to the Researcher, routes any flags to the
user, and routes any `[RESEARCHER: ...]` placeholders to the Researcher for
fact sourcing.

---

## 11. End Of Skill

This skill is the entire job of the Planner. If you follow it step by step,
you will produce a tagged script that the Researcher can turn into a sourcing
manifest, that TTS can turn into audio, and that the visual preparation
agents can turn into on-screen visuals.

When in doubt: write the audio first, justify every tag, respect the
template's proportions and frequency, and flag what you cannot determine.
