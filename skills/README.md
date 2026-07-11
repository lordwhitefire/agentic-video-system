# Skills — Classification And Structure

## The Core Principle

**Agents are WHO + WHAT. Skills are HOW. They are separate.**

An agent file says "I am the Graphics Creator. I create static graphics." It does NOT say how to create them. The HOW lives in skills, which are separate files that the agent references.

This separation lets you:
- Swap a skill without touching the agent
- Test an agent with different skills
- Build skills incrementally (research → condense into skill → test with agent)
- Keep agent files lean and stable

---

## The 3 Layers

```
AGENT (who + what)  ←  agents/ directory
    ↓ uses
CUSTOM SKILLS (how to think)  ←  skills/custom/ directory
    ↓ uses
TOOL SKILLS (how to operate)  ←  skills/tools/ directory
    ↓ executes with
TOOLS (the actual software)  ←  external (MCP servers, ffmpeg, etc.)
```

---

## Custom Skills (behavioral)

**What they are:** Skills that teach an agent HOW TO THINK about its task. They define the workflow, the decision process, the rules of engagement. They are written by us, specific to our video editing system.

**Where they live:** `skills/custom/`

**What they contain:**
- The step-by-step procedure the agent follows
- The decision rules the agent applies
- The output format the agent produces
- The hard rules (laws) the agent must obey
- The handoff protocol (what the agent passes to the next agent)

**Current custom skills:**
| Skill | Agent | Status |
|-------|-------|--------|
| `script-driven-template-extraction` | Analyzer | DONE |
| `script-driven-visual-assignment` | Planner | DONE |
| `resource-md-generation` | Researcher | DONE |
| `tts-engine-management` | TTS | TO BUILD |
| `graphic-design-protocol` | Graphics Creator | TO BUILD |
| `animation-creation-protocol` | Animation Creator | TO BUILD |
| `animated-graphic-protocol` | Animated Graphics Creator | TO BUILD |
| `video-effect-creation-protocol` | Video Effects Creator | TO BUILD |
| `clip-preparation-protocol` | Clips Preparer | TO BUILD |
| `image-preparation-protocol` | Images Preparer | TO BUILD |
| `approval-loop-protocol` | All visual agents (shared) | TO BUILD |
| `assembly-protocol` | Editor | TO BUILD |
| `audio-as-master-protocol` | Editor | TO BUILD |
| `fidelity-check-protocol` | Reviewer | TO BUILD |
| `inference-detection-protocol` | Watcher/Blocker | TO BUILD |
| `root-cause-analysis-protocol` | Investigator | TO BUILD |

**How to build a custom skill:**
1. Research the task (watch YouTube tutorials, read guides, study examples)
2. Condense the learning into a step-by-step procedure
3. Write the skill file with: purpose, procedure, output format, hard rules
4. Test the skill with its agent (give the agent a task + the skill, see what happens)
5. Iterate based on results

---

## Tool Skills (execution)

**What they are:** Skills that teach an agent HOW TO OPERATE a specific tool. They come from skill repositories like OpenMontage (1039 skills) and others. They are generic — not specific to our system.

**Where they live:** `skills/tools/`

**What they contain:**
- Which tool to use for which task
- What parameters to pass
- What the expected output looks like
- Common failure modes and fixes

**Examples:**
- "How to use ffmpeg to cut a clip from 0:03 to 0:08"
- "How to use Whisper to transcribe audio with word-level timestamps"
- "How to use the mcp-video server's 119 tools"
- "How to use Coqui XTTS-v2 to clone a voice"

**Source repositories:**
- OpenMontage (1039 skills) — general purpose
- Other skill repos (to be catalogued)

**How to add a tool skill:**
1. Find the skill in a skill repository (or write one)
2. Copy it to `skills/tools/`
3. Reference it from the agent that needs it

---

## How Agents Reference Skills

An agent file has a section like this:

```markdown
## Skills You Use

- **Custom:** `script-driven-template-extraction` (in `/skills/custom/`)
- **Tools:** Perception tools (Whisper for transcription, VLM for frame analysis)
```

The agent KNOWS it uses these skills. The skills themselves are loaded separately when the agent runs. This means:
- You can add a skill to an agent by updating the agent's "Skills You Use" section
- You can swap a skill by changing the reference
- You can test an agent with no skills (to see its raw behavior) by removing the references

---

## The Testing Workflow

This is the workflow you described for testing:

1. **Pick an agent** (e.g., the Animated Graphics Creator)
2. **Research the craft** (watch YouTube tutorials on animated graphics)
3. **Condense the learning** into a custom skill (`animated-graphic-protocol.md`)
4. **Give the agent a task + the skill**:
   ```
   Using the animated-graphic-protocol skill, create an animated graphic
   showing Mbappe's transfer from PSG to Real Madrid. Show me examples first.
   ```
5. **Evaluate the result** — did the agent follow the skill? did it produce good work?
6. **Iterate**:
   - If the agent misbehaved → modify the skill (more constraints, clearer steps)
   - If the agent did well but the output was bad → modify the skill (better procedure)
   - If the agent could not execute → check if tool skills are missing
   - If the agent's identity was wrong → modify the agent file

This is why agents and skills are separate. You test the agent with different skills until you find the combination that works. You never touch the agent file unless its IDENTITY is wrong.
