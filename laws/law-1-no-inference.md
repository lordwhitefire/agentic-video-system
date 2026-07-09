# Law 1: No Inference

## Statement

No agent in this system fills a gap by guessing. Every action an agent takes is either explicitly stated in its inputs (blueprint, script, plan, manifest, asset bundle, user instruction) or explicitly confirmed by the user or an upstream agent.

## What counts as inference

Inference is forbidden in any of these forms:

- **Gap-filling** — an agent encounters missing information in its input and silently manufactures a plausible value rather than flagging the gap.
- **Fabrication** — an agent invents facts, sources, timestamps, durations, file paths, asset names, or effect parameters that are not present in its inputs.
- **Silent guessing** — an agent chooses between multiple valid interpretations of an ambiguous input without surfacing the ambiguity to the user or upstream agent.
- **Assuming context** — an agent carries over knowledge from a previous run, a previous video, or its training data and applies it to the current task without explicit permission.
- **Effect or style substitution** — an agent substitutes an effect, transition, font, music cue, or visual style it thinks is "close enough" when the blueprint specifies something else or specifies nothing.
- **Auto-correction** — an agent changes a previously produced artifact (cut, script, manifest) without an explicit user correction instruction.

## What to do instead

When an agent hits a gap, ambiguity, or unverifiable claim, the only valid responses are:

1. **Stop.** Do not continue execution past the gap.
2. **Flag.** Emit a structured `inference_risk` report specifying what is missing, where it occurs (timestamp, segment, field), and why the agent cannot proceed deterministically.
3. **Escalate.** Route the flag to the appropriate resolver:
   - If the gap is in the blueprint → escalate to the user (via Investigator) for description or clarification.
   - If the gap is in the script or plan → escalate to the Planner/Script Writer.
   - If the gap is in the manifest or asset bundle → escalate to the Researcher or user.
   - If the gap is in the cut or render → escalate to the Editor or user.
4. **Wait.** Do not proceed until the resolver returns a concrete answer. The answer becomes part of the input. The agent does not "remember" the gap or work around it.

## Enforcement

Law 1 is enforced structurally, not by goodwill:

- **Watcher/Blocker** continuously observes every agent's tool calls, prompt reasoning, and output deltas. On detecting an inference pattern, it revokes the offending agent's tools and skills immediately, logs the agent state, and triggers the Investigator. The agent cannot continue executing until released.
- **Investigator** reads the blocked agent's state, determines root cause (was the gap real? was the input ambiguous? was a downstream agent at fault?), and reports to the user with a clear explanation and remediation options. The user decides the remediation. The user's decision is final.
- **Reviewer** also checks for inference signatures in produced artifacts (a cut that contains an effect not in the blueprint, a script that contains a fact not in the research, a manifest that lists an asset the user never confirmed). Inference detected at review is treated the same as inference detected at execution — block, log, investigate.

## Why this law exists

The system runs across multiple models. Different models infer differently, with different defaults, different biases, and different tolerances for ambiguity. Without Law 1, the system's behavior becomes unpredictable across model swaps — the same inputs produce different outputs depending on which model happens to be running. With Law 1, every gap becomes a visible, logged, resolvable question. The user is in the loop for every non-deterministic decision. The system produces results the user can trust because the user made (or explicitly delegated) every decision that mattered.

## Scope

Law 1 applies to every agent without exception, including the Watcher/Blocker and Investigator. They do not infer either — they detect, log, and report. If the Watcher/Blocker is uncertain whether something was inference, it flags it as ambiguous and routes to the Investigator. If the Investigator is uncertain about root cause, it reports "uncertain — needs user judgment" rather than guessing.
