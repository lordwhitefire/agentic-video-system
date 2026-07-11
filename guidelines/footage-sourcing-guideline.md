# Footage Sourcing Guideline (For The Human Researcher)

> **Status:** This is your operating manual. You follow it when sourcing from `resource.md`. It is not an agent skill — it is your reference document.
>
> **Companion file:** `/scripts/<project-name>-resource.md` (the manifest the Researcher agent produces)
>
> **Optional improvements:** See the bottom of this file for 5 enhancements you can choose to apply or ignore. They are not required — your human judgment already covers most of what they address.

---

## Purpose

Given a script line tagged `visual_type: b_roll` or `a_roll`, find real footage **of the
specific named subject** the line is about — not generic stock footage of an unrelated
person doing a similar action. If the line is about Mbappe, the clip must be of Mbappe.

Generic stock footage of a different person ("lazy B-roll") is a last-resort fallback only,
explicitly flagged as such — never the default.

---

## Definitions (specific to this workflow)

- **A-roll (subject-specific)**: footage of the named subject talking — an interview,
  press conference, direct address to camera.
- **B-roll (subject-specific)**: footage of the named subject doing something, not talking —
  playing, training, walking, reacting — used to illustrate what's being said about them.
- **Lazy B-roll**: generic stock footage of an unrelated person doing a similar generic
  action. Only used when no subject-specific footage can be found at all, and flagged for
  later review/replacement — never treated as an acceptable final answer.
- **Image**: a still photo of the specific subject. Must not carry a visible watermark.

Sourcing platforms: general web video platforms (YouTube, TikTok, Instagram, news
footage) and general image search. **Not** paid stock/licensing marketplaces
(Storyblocks, Envato, Artgrid, etc.) — those are explicitly out of scope for this
workflow regardless of quality.

---

## Step 1: Concretize the line

Most script lines are judgments or narrative claims, not literal visual descriptions.
Before searching, translate the line into one or more **concrete visual moments** that
would represent it.

```
Line: "Mbappe was a flop."
Concretizations (generate 2-4):
  1. Missing a clear scoring chance
  2. Being substituted early, visibly frustrated
  3. Reacting after a missed shot
  4. Being criticized in a post-match interview clip
```

```
Line: "He trains every single day, rain or shine."
Concretizations:
  1. Training in visibly bad weather
  2. Solo training footage outside of team sessions
  3. Early-morning/late-night training clips
```

If the line already IS a literal visual description ("he scored a hat-trick"), skip this
step — the concretization is the line itself.

> **Note from the manifest workflow:** The Researcher agent will already provide 2-4 concretization suggestions per entry in `resource.md`. You can use those directly, or generate your own if you see a better visual moment the Researcher missed. The suggestions are a starting point, not a constraint.

---

## Step 2: Generate search queries

Combine the **subject's name** with **each concretization**, not the line's literal
wording and not the action alone.

```
Subject: Kylian Mbappe
Queries:
  - "Mbappe missed chance"
  - "Mbappe substituted early"
  - "Mbappe frustrated reaction"
  - "Mbappe criticized interview"
```

Run each query across YouTube, TikTok, and Instagram search separately — results differ
significantly by platform.

---

## Step 3: Candidate identification

For each query, collect candidate results: title, thumbnail, platform, and link.
**This step identifies and links candidates — it does not download them.** Actual
retrieval of the clip is a separate manual step outside this skill (platform terms of
service restrict automated downloading, so this isn't automated here).

If a strong candidate can't be confirmed automatically, surface the link back to the user
for manual review rather than guessing.

---

## Step 4: Verification (identity + moment match)

A candidate must pass **two checks**, not one:

1. **Identity match** — is this actually the named subject? Cross-check the video title,
   channel/account name, and caption for the subject's name as a strong signal, and use a
   vision-capable model on the thumbnail/frame as a secondary check. Treat visual
   identification of a specific named person as a heuristic, not a certainty — the
   title/metadata signal matters as much as the visual one.
2. **Moment match** — does the clip actually show the concretized moment (not just the
   subject doing anything at all)? Score this the same way as the earlier B-roll
   verification: show the model the concretization + a thumbnail/frame, ask for a
   relevance score.

Only clips passing both checks count as valid subject-specific B-roll.

> **In practice:** You watch the clip. You confirm with your own eyes that (a) this is actually Mbappe and (b) the clip shows the concretized moment. No vision model is more reliable than your judgment on a 10-second clip — you see the full footage, not a single frame.

---

## Step 5: Image sourcing

Search general image sources (not stock marketplaces) for photos of the specific subject
matching the line's context. Before accepting an image:
- Check for a visible watermark (visual check) — reject if present
- Prefer images where the subject is clearly identifiable and matches the context (e.g.
  match-day photo vs. red-carpet photo — pick based on what the line needs)

---

## Step 6: Fallback hierarchy (in order)

1. **Exact concretized moment, subject-specific** — ideal outcome
2. **Adjacent subject-specific moment** — same subject, close-enough moment, if the exact
   one isn't found (e.g. any missed-chance clip of Mbappe, if not from the specific match
   referenced)
3. **Lazy B-roll** — generic footage of an unrelated person doing the general action.
   Only used if steps 1-2 return nothing. Must be flagged in the output
   (e.g. `lazy_broll: true`) so it's visible for review and can be swapped later.
4. **Reassign visual type** — if nothing works even at the lazy fallback level, hand the
   line back to the Video Visual Planning Skill to reassign it as an animated graphic or
   animation instead of forcing in a bad B-roll.

> **How to execute step 4 in the manifest workflow:** Do NOT force a bad clip. Leave the `link` and `local_file_path` fields blank in the manifest entry. Add a note in the `notes` field explaining what you tried. The Planner will reassign the sentence as a graphic or animation when they see the incomplete entry.

---

## Output format per line

```yaml
line: "Mbappe was a flop."
subject: "Kylian Mbappe"
concretization_used: "Being substituted early, visibly frustrated"
platform: youtube
link: <url>
identity_match: confirmed (title + visual)
moment_match_score: 8
lazy_broll: false
```

> **Manifest integration:** The `resource.md` manifest already has these fields (and a few more) in its yaml fill-in block. Fill them in as you source each entry. The Researcher agent has already populated the `line`, `subject`, and concretization suggestions — you fill in the rest.

---

## When to invoke this guideline

Invoke for every script line tagged `visual_type: b_roll` or `a_roll` where a specific
named subject is involved, after the Video Visual Planning Skill has assigned visual
types. If verification fails at every fallback level, hand the line back to the Video
Visual Planning Skill rather than leaving it unresolved.

---

# Optional Enhancements (Apply Or Ignore)

These 5 enhancements were flagged during the skill review. You can choose to apply them when sourcing, or ignore them — your human judgment already covers most of what they address. They are listed here so you have them in mind, not because they are mandatory.

## Enhancement 1: Post-download moment verification

The guideline says to verify moment match from a thumbnail. In practice, a thumbnail is one frame and cannot confirm a MOMENT. Apply this enhancement:

- **Before download:** Use title + caption + channel as the moment signal (Tier A). This is your pre-download gate.
- **After download:** Scrub the video and sample frames at multiple timestamps to confirm the concretized moment actually appears (Tier B). If Tier B fails after download, reject the clip and continue down the fallback chain.

You probably already do this intuitively. The enhancement just makes it explicit.

## Enhancement 2: Duration check against the sentence

The `resource.md` manifest includes a `Required minimum duration` field per entry (calculated from the Planner's sentence estimate). Apply this enhancement:

- Before accepting a clip, confirm its duration is at least the required minimum.
- If the clip is shorter than the sentence's audio, it leaves a gap when placed against the narration.
- If no clip meets the minimum, fall through to the next fallback level.

The manifest already gives you the number. Just check it.

## Enhancement 3: Resolution floor

A 240p clip with compression artifacts is unusable in a 1080p export. Apply this enhancement:

- Minimum resolution: 720p preferred, 480p absolute floor.
- Reject candidates below 480p — even if they are the only subject-specific option.
- If the only available clip is below floor, fall through to lazy B-roll or reassignment.

You can usually tell resolution from the platform's quality selector before downloading.

## Enhancement 4: Deduplication across entries

The manifest's No Reuse constraint (Law 9) means each clip is used at most ONCE per video. Apply this enhancement:

- Keep a running list (mental or written) of every clip URL you have already used in this project.
- Before accepting a new clip, check it against the list.
- If the same URL or same source video is already used → reject and continue searching.
- This prevents the video from feeling repetitive (same Mbappe subbed-off clip appearing 3 times).

The manifest's constraints field will remind you when an entry is at risk of reuse (e.g., "Do not reuse the clip sourced for Entry #1").

## Enhancement 5: Watermark check on video clips, not just images

The guideline checks images for watermarks in Step 5 but does not explicitly check video clips. Video clips from YouTube/TikTok/Instagram frequently have:
- Creator channel logos burned into a corner
- Platform watermarks (TikTok logo is burned in on downloads)
- News channel lower-thirds
- Reaction channel overlays

Apply this enhancement:

- After downloading a video clip, scrub through it and check for burned-in logos, branding, or watermarks in any corner.
- If you see a persistent burned-in mark → reject the clip and continue down the fallback chain.
- TikTok downloads in particular almost always have the TikTok logo burned in — prefer YouTube or news footage when available.

This is Law 10 (no watermarked images) extended to video. Your eyes are more reliable than any automated check here.

---

# End Of Guideline

This document is your reference. Keep it open while sourcing from `resource.md`. When in doubt, the fallback hierarchy (Step 6) is your escape hatch — never force a bad clip.
