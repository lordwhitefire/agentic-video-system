
---

## Error #020 — Image reusing in graphics (no reusing policy)

### The error

The Editor reused the same images across multiple animated graphics. Specifically:
- `mbappe-world-cup-celebration.jpg` used in 6 different graphics (ag01, ag04, ag06, ag09, ag11, ag13)
- `mbappe-club-frustration.jpg` used in 6 different graphics (ag02, ag03, ag07, ag10, ag12, ag13)
- `pressing-stats-graphic.png` used in 2 graphics (ag08, ag15)

### The rule (NEW)

**No reusing policy:** Each graphic must use a DIFFERENT image. Images cannot be reused across graphics. If we have 15 graphics, we need at least 15 distinct images (or source more images).

### Why this matters

- Reusing the same image makes the video feel repetitive and cheap
- Professional broadcast graphics never reuse the same photo in different contexts
- Each graphic should feel unique — different visual context for each point being made

### The fix

1. Source more images (at least 10-15 more) so each graphic has a unique image
2. Update the Editor and Planner agent definitions with the no-reusing rule
3. Before generating graphics, verify each image is used in only ONE graphic

### Status

Rule documented. Need to source more images before regenerating graphics.

---

## Error #021 — Watermarked image used in graphics (AGAIN)

### The error

The Alamy watermarked version of `mbappe-world-cup-celebration.jpg` was used in the animated graphics (ag01, ag06, ag13) — even though the file was replaced with a clean version in a previous fix (commit `836a8a0`).

### Root cause

During git merge operations, the old watermarked version of the image was picked up by the graphics generation script. The timeline:
1. Image replaced with clean version (commit `836a8a0`)
2. Repo wiped and re-cloned (fresh start)
3. During the fresh clone, the clean version was present on disk
4. BUT: a git merge during push brought back a conflicting version
5. Graphics were generated with whatever version was on disk at generation time
6. VLM confirmed: standalone image file is CLEAN, but graphics frames show ALAMY watermark

The graphics generation script read the file at the wrong moment, or a git merge conflict resolved to the watermarked version.

### The fix

1. Verify the clean image is on disk (done — VLM confirmed standalone file is clean)
2. Regenerate ALL graphics that use the celebration image (ag01, ag04, ag06, ag09, ag11, ag13)
3. After regeneration, VLM-verify the graphics frames for watermarks
4. Going forward: ALWAYS VLM-check the actual graphics frames (not just the source images) before committing

### Lesson

Don't just check the source image for watermarks — check the FINAL OUTPUT (the graphic/video frame). The source image might be clean but a stale version could be used during generation. Always verify the rendered output.

### Prevention

After generating ANY graphic or video, extract a frame and VLM-check for watermarks BEFORE committing. This should be a standard post-generation step in the Editor workflow.
