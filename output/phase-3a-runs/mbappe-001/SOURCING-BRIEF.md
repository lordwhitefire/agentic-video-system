# Sourcing Brief — mbappe-001
## For: User (manual sourcing of video clips + audio)

**Created by:** Researcher agent
**Date:** 2026-07-09
**Run:** mbappe-001 — "What's Wrong with Mbappé?"

---

## How to use this file

For each asset below, you need to:
1. **Find** a video clip (or audio track) matching the description
2. **Download** it (YouTube, stock footage sites, etc.)
3. **Upload** it to the folder specified in "Upload Location"
4. **Name** it exactly as specified in "Filename"
5. **Tell me** when you're done — I'll verify and hand off to the Editor

**CRITICAL — Source longer than needed:**
For each clip, I list:
- **Duration needed:** How long the final cut will use (e.g., 4 seconds)
- **Source duration to provide:** How long the raw clip should be (e.g., 15-20 seconds)

Always source LONGER than needed. The Editor will pick the best 4 seconds from your 15-20 second clip. This is standard editing practice — you don't supply the exact length, you supply enough for the editor to choose the best moment.

**Licensing reminder:** You're the human in the loop for licensing. Only source clips you have the right to use (your own footage, properly licensed stock, fair use commentary clips, etc.). The system trusts your judgment here — that's why you're the human in the loop.

---

## Upload Location

Upload all video clips to:
```
agentic-video-system/output/phase-3a-runs/mbappe-001/assets/clips/
```

Upload the audio track to:
```
agentic-video-system/output/phase-3a-runs/mbappe-001/assets/audio/
```

Then commit and push to GitHub:
```bash
cd agentic-video-system
git add output/phase-3a-runs/mbappe-001/assets/clips/
git add output/phase-3a-runs/mbappe-001/assets/audio/
git commit -m "Phase 3a: user-sourced video clips and audio for mbappe-001"
git push
```

---

## Video Clips to Source (17 total)

### SEGMENT 1 — COLD OPEN (8 seconds)

#### clip-001: Mbappé World Cup celebration
- **Filename:** `clip-001-mbappe-world-cup-celebration.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Mbappé celebrating a goal for France in a World Cup match. Joyful, triumphant, arm raised or sliding on knees. Should clearly show Mbappé in a France jersey.
- **Duration needed:** 4 seconds (final cut)
- **Source duration to provide:** 15-20 seconds (so editor can pick the best celebration moment)
- **Search hints:**
  - "Mbappé 2018 World Cup goal celebration"
  - "Mbappé 2022 World Cup celebration"
  - "Mbappé France goal celebration slide"
  - "Mbappé hat-trick 2022 final celebration"
- **Suggested sources:** YouTube (search highlights), FIFA official highlights, L'Équipe highlights
- **Notes:** The clip will be used in a split-screen with clip-002 (frustration). Pick something visually distinct — bright, energetic, clearly a celebration.

#### clip-002: Mbappé club frustration
- **Filename:** `clip-002-mbappe-club-frustration.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Mbappé looking frustrated, disappointed, or head down at club level (PSG or Real Madrid). Should show negative emotion — head down, hands on hips, looking away, walking off pitch.
- **Duration needed:** 4 seconds (final cut)
- **Source duration to provide:** 15-20 seconds
- **Search hints:**
  - "Mbappé frustrated PSG Champions League exit"
  - "Mbappé head down Real Madrid"
  - "Mbappé disappointed substitution"
  - "Mbappé walking off pitch sad"
- **Suggested sources:** YouTube match highlights, post-match footage
- **Notes:** This is the RIGHT side of the split-screen (contrast to clip-001's celebration). Pick something clearly emotional — head down, frustrated body language.

---

### SEGMENT 2 — HOOK (52 seconds)

#### clip-003: Mbappé 2018 World Cup goal
- **Filename:** `clip-003-mbappe-2018-world-cup-goal.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Mbappé scoring a goal in the 2018 World Cup. The goal itself — the shot, the ball hitting the net. Preferably the goal vs Argentina (his breakout performance) or the final vs Croatia.
- **Duration needed:** 3 seconds (final cut)
- **Source duration to provide:** 10-15 seconds (include the run-up, shot, and net)
- **Search hints:**
  - "Mbappé 2018 World Cup goal vs Argentina"
  - "Mbappé 2018 World Cup final goal"
  - "Mbappé 2018 goal compilation"
- **Suggested sources:** YouTube, FIFA highlights
- **Notes:** The shot + ball in net is the key moment. Editor will pick the most visually striking angle.

#### clip-004: Mbappé 2022 World Cup final hat-trick
- **Filename:** `clip-004-mbappe-2022-final-hat-trick.mp4`
- **Upload to:** `assets/clips/`
- **Description:** One of Mbappé's three goals in the 2022 World Cup final vs Argentina. The penalty, the volley, or the second penalty. The goal moment itself.
- **Duration needed:** 3 seconds (final cut)
- **Source duration to provide:** 10-15 seconds (include approach, shot, net)
- **Search hints:**
  - "Mbappé 2022 World Cup final hat-trick"
  - "Mbappé vs Argentina 2022 final goals"
  - "Mbappé 2022 final penalty"
  - "Mbappé 2022 final volley"
- **Suggested sources:** YouTube, FIFA highlights
- **Notes:** Any of the three goals works. The volley is the most visually spectacular, but any is fine. Editor will pick the best angle.

#### clip-005: PSG Champions League failure
- **Filename:** `clip-005-psg-ucl-failure.mp4`
- **Upload to:** `assets/clips/`
- **Description:** PSG's Champions League elimination during the Mbappé era. The moment of elimination — final whistle, players devastated, Mbappé walking off. Could be vs Real Madrid (2022), vs Bayern (2023), or any UCL exit 2018-2024.
- **Duration needed:** 3 seconds (final cut)
- **Source duration to provide:** 15-20 seconds (include the elimination moment + aftermath)
- **Search hints:**
  - "PSG Champions League elimination Mbappé"
  - "PSG UCL exit Real Madrid 2022"
  - "PSG Bayern Munich UCL exit"
  - "Mbappé PSG UCL disappointment"
- **Suggested sources:** YouTube match highlights
- **Notes:** The elimination moment is key — whistle blown, heads drop, Mbappé walking off.

#### clip-006: Real Madrid Mbappé struggle
- **Filename:** `clip-006-mbappe-madrid-struggle.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Mbappé at Real Madrid (2024-25 season) in a moment of struggle — missing a chance, looking frustrated, team conceding. Should show the difficulties, not the goals.
- **Duration needed:** 3 seconds (final cut)
- **Source duration to provide:** 15-20 seconds
- **Search hints:**
  - "Mbappé Real Madrid 2024 struggle"
  - "Mbappé Madrid miss chance"
  - "Real Madrid Mbappé tactical issues"
  - "Mbappé Madrid frustrated match"
- **Suggested sources:** YouTube match highlights
- **Notes:** The contrast to World Cup success. Pick a moment of frustration or tactical breakdown, not a goal.

---

### SEGMENT 4 — ACT 1: WHAT THE WORLD CUP GIVES HIM (106 seconds)

#### clip-007: France national team chemistry
- **Filename:** `clip-007-france-team-chemistry.mp4`
- **Upload to:** `assets/clips/`
- **Description:** France national team showing chemistry — Mbappé with Griezmann, Giroud, or other teammates. Team huddle, celebration together, tactical discussion. Should show unity and structure.
- **Duration needed:** 5 seconds (final cut)
- **Source duration to provide:** 20-30 seconds (include multiple moments of interaction)
- **Search hints:**
  - "France national team huddle World Cup"
  - "Mbappé Griezmann Giroud France"
  - "France team celebration World Cup 2018"
  - "France team chemistry Deschamps"
- **Suggested sources:** YouTube, FIFA highlights
- **Notes:** The point is to show a FUNCTIONING SYSTEM — players working together, clear roles, unity. Not just Mbappé alone.

#### clip-008: Deschamps on the sideline
- **Filename:** `clip-008-deschamps-sideline.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Didier Deschamps on the France sideline — giving instructions, celebrating, or looking focused. Should show him as the authoritative figure who built the system.
- **Duration needed:** 3 seconds (final cut)
- **Source duration to provide:** 10-15 seconds
- **Search hints:**
  - "Deschamps sideline France World Cup"
  - "Deschamps tactical instructions France"
  - "Deschamps celebrating France goal"
- **Suggested sources:** YouTube, FIFA highlights
- **Notes:** Deschamps is the architect of the system. Show him in command — clipboard, instructions, or celebration.

---

### SEGMENT 5 — ACT 2: WHY CLUBS BREAK AROUND HIM (160 seconds)

#### clip-009: PSG MNM trio (Mbappé, Neymar, Messi)
- **Filename:** `clip-009-psg-mnm-trio.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Mbappé, Neymar, and Messi together at PSG — on the pitch, in training, or celebrating. Should show all three (or at least Mbappé with one of them). The "MNM" era.
- **Duration needed:** 5 seconds (final cut)
- **Source duration to provide:** 20-30 seconds
- **Search hints:**
  - "PSG Mbappé Neymar Messi together"
  - "PSG MNM trio"
  - "Mbappé Neymar PSG celebration"
  - "PSG 2021-22 Mbappé Messi Neymar"
- **Suggested sources:** YouTube, PSG official
- **Notes:** The point is to show the talent that was supposed to work together — but didn't. Show all three if possible.

#### clip-010: Mbappé and Vinícius left wing overlap
- **Filename:** `clip-010-mbappe-vinicius-overlap.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Mbappé and Vinícius Jr. at Real Madrid, both on the left wing, overlapping or getting in each other's way. The tactical collision. Should show both players in the left channel.
- **Duration needed:** 5 seconds (final cut)
- **Source duration to provide:** 20-30 seconds (include multiple moments of the overlap)
- **Search hints:**
  - "Mbappé Vinícius Real Madrid left wing"
  - "Mbappé Vinícius overlap Madrid 2024"
  - "Real Madrid Mbappé Vinícius tactical"
  - "Mbappé Vinícius same space Madrid"
- **Suggested sources:** YouTube tactical analysis videos, match highlights
- **Notes:** This is the key tactical visual — two world-class left wingers in the same space. If you can find a tactical analysis video that highlights this, even better.

#### clip-011: Bellingham dropping deep
- **Filename:** `clip-011-bellingham-dropping-deep.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Jude Bellingham at Real Madrid dropping deep to collect the ball, covering defensively, or filling gaps. Should show him in a deeper position than his usual advanced role — compensating for Mbappé's presence.
- **Duration needed:** 3 seconds (final cut)
- **Source duration to provide:** 15-20 seconds
- **Search hints:**
  - "Bellingham Real Madrid defensive work"
  - "Bellingham dropping deep Madrid"
  - "Bellingham covering midfield Madrid 2024"
- **Suggested sources:** YouTube match highlights, tactical analysis
- **Notes:** The point is that Bellingham's role changed — he became a utility piece, not the advanced playmaker he was before Mbappé arrived. Show him working defensively or deep.

---

### SEGMENT 6 — ACT 3: THE TACTICAL COST (134 seconds)

#### clip-012: Mbappé not pressing
- **Filename:** `clip-012-mbappe-not-pressing.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Mbappé walking or standing during a defensive phase — NOT pressing, NOT tracking back. Should show the lack of defensive effort. The moment when the team is defending and Mbappé is just watching or walking.
- **Duration needed:** 3 seconds (final cut)
- **Source duration to provide:** 15-20 seconds (include the defensive phase context)
- **Search hints:**
  - "Mbappé not pressing"
  - "Mbappé walking defending"
  - "Mbappé defensive effort criticism"
  - "Mbappé lazy defending PSG Madrid"
- **Suggested sources:** YouTube tactical analysis, match highlights
- **Notes:** This is the visual evidence of the tactical cost. The Editor will use it to show what the stats mean. Pick a clear moment where Mbappé is visibly not participating in the press.

---

### SEGMENT 7 — ACT 4: THE PATTERN (166 seconds)

#### clip-013: PSG manager (Tuchel, Pochettino, Galtier, or Enrique)
- **Filename:** `clip-013-psg-manager.mp4`
- **Upload to:** `assets/clips/`
- **Description:** One of PSG's managers during the Mbappé era — Thomas Tuchel, Mauricio Pochettino, Christophe Galtier, or Luis Enrique. On the sideline, in a press conference, or giving instructions. Should show a manager who was eventually fired/let go.
- **Duration needed:** 4 seconds (final cut)
- **Source duration to provide:** 15-20 seconds
- **Search hints:**
  - "Tuchel PSG sideline"
  - "Pochettino PSG press conference"
  - "Galtier PSG touchline"
  - "Luis Enrique PSG instructions"
- **Suggested sources:** YouTube, PSG official
- **Notes:** Any of the four works. The point is the CYCLE — managers who came, tried to build a system, and left. Pick whichever you can find good footage of.

#### clip-014: Real Madrid manager (Ancelotti or Alonso)
- **Filename:** `clip-014-madrid-manager.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Carlo Ancelotti or Xabi Alonso at Real Madrid — on the sideline, in a press conference, or giving instructions. Should show a manager dealing with the Mbappé situation.
- **Duration needed:** 4 seconds (final cut)
- **Source duration to provide:** 15-20 seconds
- **Search hints:**
  - "Ancelotti Real Madrid sideline"
  - "Ancelotti Mbappé press conference"
  - "Xabi Alonso Real Madrid"
- **Suggested sources:** YouTube, Real Madrid official
- **Notes:** Ancelotti is the more established figure (his "dressing room harmony" is mentioned in the script). Alonso is the one who was fired mid-season. Either works — pick whichever you find better footage of.

---

### SEGMENT 8 — ACT 5: WHY FRANCE DOESN'T HAVE THIS PROBLEM (79 seconds)

#### clip-015: France team huddle / unity
- **Filename:** `clip-015-france-huddle-unity.mp4`
- **Upload to:** `assets/clips/`
- **Description:** France national team in a huddle, celebrating together, or showing unity. The contrast to club dysfunction — at France, the system works, the team is together.
- **Duration needed:** 4 seconds (final cut)
- **Source duration to provide:** 15-20 seconds
- **Search hints:**
  - "France team huddle World Cup"
  - "France celebration unity Mbappé"
  - "France national team together"
  - "Deschamps France team talk"
- **Suggested sources:** YouTube, FIFA highlights
- **Notes:** This is the emotional payoff — France as a FUNCTIONING SYSTEM. Show players together, huddled, celebrating as one. Mbappé should be part of the group, not above it.

---

### SEGMENT 9 — ACT 6: THE VERDICT (92 seconds)

#### clip-016: Mbappé in France kit, determined
- **Filename:** `clip-016-mbappe-france-determined.mp4`
- **Upload to:** `assets/clips/`
- **Description:** Mbappé in a France kit, looking determined, focused, or intense. Looking at the camera or at the pitch. Should be a portrait-style shot — close-up of his face showing focus.
- **Duration needed:** 4 seconds (final cut)
- **Source duration to provide:** 15-20 seconds
- **Search hints:**
  - "Mbappé France kit determined"
  - "Mbappé focused World Cup"
  - "Mbappé France national team portrait"
  - "Mbappé intense France match"
- **Suggested sources:** YouTube, FIFA highlights
- **Notes:** This is the "verdict" moment — will he carry this World Cup? Show him looking ready, focused, determined. A portrait-style close-up works best.

#### clip-017: World Cup trophy
- **Filename:** `clip-017-world-cup-trophy.mp4`
- **Upload to:** `assets/clips/`
- **Description:** The FIFA World Cup trophy — being lifted, on display, or in a celebration. Should be a clear, iconic shot of the trophy itself.
- **Duration needed:** 2 seconds (final cut)
- **Source duration to provide:** 10-15 seconds
- **Search hints:**
  - "FIFA World Cup trophy lift"
  - "World Cup trophy celebration"
  - "World Cup trophy close up"
- **Suggested sources:** YouTube, FIFA official
- **Notes:** The trophy is the visual symbol of what's at stake. A clear, iconic shot — ideally being lifted or held aloft.

---

## Audio to Source (1 track)

#### audio-001: Background music bed
- **Filename:** `audio-001-background-music.mp3` (or `.wav`)
- **Upload to:** `assets/audio/`
- **Description:** Instrumental background music for a 12-14 minute analytical commentary video. Mood: analytical, slightly tense, building, no vocals. Think "documentary underscore" or "tactical analysis background."
- **Duration needed:** 12-14 minutes (full video length)
- **Source duration to provide:** 12-14 minutes (or a loopable 3-4 minute track that can be extended)
- **Search hints:**
  - "royalty free documentary background music"
  - "analytical commentary underscore instrumental"
  - "tension building instrumental no vocals"
  - "sports analysis background music"
- **Suggested sources:** 
  - YouTube Audio Library (free, no copyright)
  - Epidemic Sound (paid, but high quality)
  - Artlist (paid)
  - Free Music Archive (free, check license)
  - Incompetech (Kevin MacLeod, free with attribution)
- **Licensing:** Must be royalty-free or properly licensed. The Editor will duck it under the voice track. If you can't find a 12-14 minute track, a 3-4 minute loopable track works — the Editor can extend it.
- **Notes:** The music should NOT overpower the voice. It's a bed, not a feature. Pick something subtle — piano, strings, ambient. Avoid anything with a strong beat that competes with speech.

---

## Summary

| Asset Type | Count | Total Source Duration (approx.) |
|---|---|---|
| Video clips | 17 | ~4-5 minutes of raw footage |
| Audio | 1 track | 12-14 minutes (or 3-4 min loopable) |
| **Total** | **18 assets** | |

## What's already sourced (no action needed)

- **5 images** (already sourced by Researcher via web image search, VLM-verified):
  - Mbappé World Cup celebration still
  - Mbappé club frustration still
  - France 4-2-3-1 formation graphic
  - Mbappé/Vinícius heat map
  - Pressing stats graphic
- **6 graphics** (will be generated by the Editor):
  - Title cards: "WORLD CUP HERO. CLUB FLOP.", "WHY?", "IT'S NOT ABILITY. IT'S CONTEXT.", "THE SYSTEM IS BIGGER THAN THE STAR."
  - Comparison graphic: "FRANCE: WEAPON IN A SYSTEM. CLUBS: SYSTEM AROUND A WEAPON."
  - PSG manager timeline graphic

## After you upload

When you've uploaded all the clips and audio (or as many as you can find — flag any you can't), tell me:
1. **Which clips you uploaded** (by filename)
2. **Which clips you couldn't find** (so I can mark them as unavailable and the Editor can adjust)
3. **Any notes about the clips** (e.g., "clip-010 is actually a tactical analysis video, not raw match footage — that's better")

I'll then:
1. **Verify** each clip with VLM (vision read the first frame)
2. **Update** the Asset Bundle with verification status
3. **Hand off** to the Editor agent, who will:
   - Generate the title cards and graphics
   - Cut the video following the Blueprint's template structure
   - Sync the TTS voice track (your cloned voice)
   - Composite everything into the final video

---

## Quick checklist (print this)

- [ ] clip-001: Mbappé World Cup celebration (4s needed, 15-20s source)
- [ ] clip-002: Mbappé club frustration (4s needed, 15-20s source)
- [ ] clip-003: Mbappé 2018 World Cup goal (3s needed, 10-15s source)
- [ ] clip-004: Mbappé 2022 final hat-trick goal (3s needed, 10-15s source)
- [ ] clip-005: PSG Champions League failure (3s needed, 15-20s source)
- [ ] clip-006: Real Madrid Mbappé struggle (3s needed, 15-20s source)
- [ ] clip-007: France national team chemistry (5s needed, 20-30s source)
- [ ] clip-008: Deschamps on sideline (3s needed, 10-15s source)
- [ ] clip-009: PSG MNM trio (5s needed, 20-30s source)
- [ ] clip-010: Mbappé/Vinícius left wing overlap (5s needed, 20-30s source)
- [ ] clip-011: Bellingham dropping deep (3s needed, 15-20s source)
- [ ] clip-012: Mbappé not pressing (3s needed, 15-20s source)
- [ ] clip-013: PSG manager (4s needed, 15-20s source)
- [ ] clip-014: Real Madrid manager (4s needed, 15-20s source)
- [ ] clip-015: France team huddle/unity (4s needed, 15-20s source)
- [ ] clip-016: Mbappé in France kit, determined (4s needed, 15-20s source)
- [ ] clip-017: World Cup trophy (2s needed, 10-15s source)
- [ ] audio-001: Background music bed (12-14 min, or 3-4 min loopable)

**Upload to:** `agentic-video-system/output/phase-3a-runs/mbappe-001/assets/clips/` (and `assets/audio/` for the music)
**Then:** `git add`, `git commit`, `git push`
**Then:** Tell me you're done
