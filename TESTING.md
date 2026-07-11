# Testing Guide — How To Test Agents Individually

## The Goal

You are not running the full pipeline yet. You are testing ONE agent at a time, with ONE skill at a time, to see if it behaves the way you want. This is iterative development: test, evaluate, modify the skill (or the agent), test again.

## The Testing Loop

```
1. Pick an agent
2. Research the craft (YouTube, tutorials, examples)
3. Write or update the custom skill for that agent
4. Give the agent a task + the skill
5. Evaluate the result
6. Modify the skill (or agent) based on what you saw
7. Repeat until satisfied
```

---

## How To Test Each Agent

### Testing The Visual Agents (05-10)

These are the agents you most want to test. They all follow the approval-loop pattern: show examples, get approval, then create.

**Test session template:**

```
You: I am testing the [AGENT NAME] agent.
     Using the [SKILL NAME] skill, [SPECIFIC TASK].
     Show me examples first before creating anything.

Agent: [should show examples, explain plan, wait for approval]

You: [give feedback — "I like style B", "can you make it darker?", etc.]

Agent: [adjusts, shows again]

You: "Go ahead, create it."

Agent: [creates the visual]

You: [evaluate the result]
```

### Example Test: Animated Graphics Creator

**Setup:** Make sure `skills/custom/animated-graphic-protocol.md` exists. If it doesn't yet, create a minimal version first (you'll refine it through testing).

**Test prompt:**
```
I am testing the Animated Graphics Creator agent.

Using the animated-graphic-protocol skill, create an animated graphic
for this sentence: "Mbappe moved from PSG to Real Madrid in 2024."

The graphic should show the PSG logo, then an arrow, then the Real
Madrid logo, appearing in sequence as the words are spoken.

Show me examples of reveal styles first. Do not create the final
graphic until I approve a style.
```

**What to evaluate:**
- Did the agent show examples BEFORE creating? (If it created first, the approval-loop-protocol skill is missing or not followed)
- Were the examples relevant? (Different reveal styles, not just one option)
- Did the agent explain its plan in plain language?
- Did the agent wait for your approval?
- After approval, did the agent produce the graphic in the approved style?
- Does the graphic contain image elements (logos)? (Law 7)
- Is the graphic watermarked? (Law 9 — should not be)

**If the agent failed:**
- If it didn't show examples → the approval-loop-protocol skill is missing or incomplete. Build it.
- If the examples were bad → the animated-graphic-protocol skill needs better example generation steps. Refine it.
- If the final graphic was wrong → the skill's production steps need refinement.
- If the agent didn't know which tools to use → tool skills are missing. Research and add them.

### Example Test: Clips Preparer

**Test prompt:**
```
I am testing the Clips Preparer agent.

I have a 20-second clip at /path/to/clip.mp4 of Mbappe missing a shot.

The script sentence is: "Mbappe was a flop."
The audio timestamp for this sentence is 1:32 to 1:45 (13 seconds).

Using the clip-preparation-protocol skill, prepare this clip.
Find the best 13 seconds. Show me what you cut before finalizing.
```

**What to evaluate:**
- Did the agent find the most relevant 13 seconds (the actual miss)?
- Did the agent show you the cut before finalizing?
- Did the agent normalize the clip (correct codec, framerate, resolution)?
- Is the clip watermarked? (Law 9)

### Example Test: Graphics Creator

**Test prompt:**
```
I am testing the Graphics Creator agent.

Using the graphic-design-protocol skill, create a static graphic for
this sentence: "His salary was 50 million euros."

The graphic should show the number 50M with a euro symbol, on a
branded background, with an image of Mbappe.

Show me design examples first. I want to see 3 different layout
options before you create the final.
```

**What to evaluate:**
- Did it show 3 layout options?
- Does each option contain an image? (Law 7)
- Are the options actually different (not just color swaps)?
- Did it wait for approval?

---

## How To Test The Thinking Agents (01-03)

These agents have completed skills. Test them to verify the skills work.

### Example Test: Analyzer

**Test prompt:**
```
I am testing the Analyzer agent.

Using the script-driven-template-extraction skill, analyze this
reference video: /path/to/reference.mp4

Produce the template JSON. Flag anything you cannot determine —
do not guess.
```

**What to evaluate:**
- Did it produce the template JSON in the correct format?
- Did it anchor on the transcript (not on visuals)?
- Did it flag unknowns instead of guessing? (Law 1)
- Do the decision rules cite specific beats? (Law 11)
- Do the visual proportions sum to 1.0?

### Example Test: Planner

**Test prompt:**
```
I am testing the Planner agent.

Using the script-driven-visual-assignment skill, write a tagged
script on the topic "Mbappe's move to Real Madrid" using the
template at /templates/mbappe-001.json.

Write the full script first, then assign visual tags. Do not
assign tags while writing.
```

**What to evaluate:**
- Did it write the full script BEFORE tagging?
- Does every sentence have exactly one primary visual tag?
- Are the proportions within ±5% of the template?
- Are authority clips placed at the right frequency?
- Did it flag unknowns instead of guessing?

---

## How To Test The Audio Agent (04)

### Example Test: TTS

**Test prompt:**
```
I am testing the TTS agent.

Using the tts-engine-management skill, generate audio for this
script: /scripts/test-script.md

Use my cloned voice (sample at /path/to/voice-sample.wav).
Produce one continuous audio file. Do not split the audio.
Run Whisper on the final audio to produce word-level timestamps.
```

**What to evaluate:**
- Is the audio one continuous file (not chunks)?
- Are the timestamps accurate?
- Did it flag any engine switches? (Law 6)
- Does the voice sound like the user's sample?

---

## How To Test The Enforcement Agents (12-14)

These agents are harder to test in isolation because they monitor other agents. Test them by giving them a scenario to evaluate.

### Example Test: Reviewer

**Test prompt:**
```
I am testing the Reviewer agent.

Using the fidelity-check-protocol skill, review this video:
/path/to/video.mp4

Check it against this script: /scripts/test-script.md
And this template: /templates/mbappe-001.json

Produce a review report with a PASS / REVISE / BRANCH decision.
```

### Example Test: Watcher/Blocker

**Test prompt:**
```
I am testing the Watcher/Blocker agent.

Here is a log of an agent's work: [paste log]

Using the inference-detection-protocol skill, identify any
inference patterns in this log. Flag any steps where the agent
guessed instead of verifying.
```

---

## Evaluating Results

After each test, ask yourself:

1. **Did the agent follow its identity?** (Did the Graphics Creator create graphics? Did the Analyzer analyze?)
2. **Did the agent follow its skill?** (Did it follow the steps in the skill file?)
3. **Did the agent obey the laws?** (No guessing, no silent substitution, no watermarked output, etc.)
4. **Was the output good?** (Does the graphic look good? Does the clip show the right moment?)
5. **Did the agent interact with you correctly?** (For visual agents: did it show examples first?)

### If the agent misbehaved:
- **The skill is incomplete or unclear** → refine the skill (most common fix)
- **The agent's identity is wrong** → modify the agent file (rare)
- **The agent lacks tool knowledge** → add tool skills
- **The agent lacks context** → check if you gave it everything it needs

### If the output was bad but the agent behaved correctly:
- **The skill's procedure is wrong** → refine the skill's steps
- **The tools are inadequate** → research better tools
- **The task itself was ambiguous** → refine the test prompt

---

## The Research Phase (Before Testing)

Before you can test a visual agent, you need to understand the craft yourself. The agent can only be as good as the skill it follows, and the skill can only be as good as your understanding of the craft.

For each visual agent, research first:

1. **Watch YouTube tutorials** on the craft (graphic design for videos, animation, video effects, clip editing, image editing)
2. **Study examples** of good work in that craft
3. **Note the vocabulary** — what terms do professionals use? (This helps you give feedback to the agent)
4. **Note the common patterns** — what are the standard approaches?
5. **Condense your learning** into a custom skill file
6. **Then test** the agent with that skill

### YouTube Search Keywords For Each Craft

#### Graphics Creator
- "video graphic design tutorial"
- "lower third after effects"
- "text overlay video premiere pro"
- "stat card design video"
- "quote card video editing"

#### Animation Creator
- "motion graphics tutorial after effects"
- "logo animation after effects"
- "2D animation for video"
- "motion graphics premiere pro"
- "kinetic typography tutorial"

#### Animated Graphics Creator
- "sequential reveal after effects"
- "animated lower third tutorial"
- "logo transition animation"
- "text reveal animation video"
- "motion graphics for narration"

#### Video Effects Creator
- "video effects tutorial after effects"
- "glitch effect video"
- "zoom punch effect"
- "word repetition effect video"
- "freeze frame with text overlay"

#### Clips Preparer
- "video editing tutorial premiere pro"
- "how to cut video ffmpeg"
- "zoom and pan video editing"
- "speed ramp tutorial"
- "color correction video"

#### Images Preparer
- "image editing for video"
- "ken burns effect tutorial"
- "image side by side video"
- "text overlay on image"
- "image color grading video"

---

## Iterating

Testing is iterative. You will not get it right the first time. The loop is:

1. Test → 2. Evaluate → 3. Refine skill → 4. Test again

Each iteration teaches you something. Each refinement makes the skill better. After 3-5 iterations, the skill should be solid enough that the agent consistently produces good work.

Do not try to perfect a skill before testing. Test with a rough skill, learn from the results, refine, test again. This is faster than trying to write a perfect skill from theory.
