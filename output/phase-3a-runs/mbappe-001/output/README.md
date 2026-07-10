# Final Video Output — mbappe-001

## "What's Wrong with Mbappé?"

The final video is split into 2 parts (each under GitHub's 100MB limit):

| File | Duration | Size |
|------|----------|------|
| `mbappe-001-part1.mp4` | 3:35 (215s) | 98 MB |
| `mbappe-001-part2.mp4` | 3:36 (216s) | 83 MB |
| **Total** | **7:10 (431s)** | **181 MB** |

## How to watch

**Option 1 — Watch parts separately:**
- Part 1: segments 1-5 (cold open through Act 2)
- Part 2: segments 6-10 (Act 3 through conclusion)

**Option 2 — Concatenate into one file:**
```bash
# Create concat list
echo "file 'mbappe-001-part1.mp4'" > concat.txt
echo "file 'mbappe-001-part2.mp4'" >> concat.txt

# Concatenate
ffmpeg -f concat -safe 0 -i concat.txt -c copy mbappe-001-full.mp4
```

## Video specs
- Resolution: 1920x1080 @ 30fps
- Video codec: H.264
- Audio: AAC (voice + background music at 15% volume)
- Voice: Coqui XTTS-v2 with user's cloned voice

## Contents
1. Cold open — Mbappé paradox (World Cup hero, club flop)
2. Hook — The pattern
3. Thesis — "It's not ability, it's context"
4. Act 1 — What the World Cup gives him
5. Act 2 — Why clubs break around him
6. Act 3 — The tactical cost
7. Act 4 — The pattern across clubs and country
8. Act 5 — Why France doesn't have this problem
9. Act 6 — The verdict: can he carry this World Cup?
10. Conclusion — "The system is bigger than the star"
