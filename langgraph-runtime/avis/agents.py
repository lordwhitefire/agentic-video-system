"""The 14 agents — the registry (WORKSPACE_REBUILD_PLAN W1).

Org (metadata only — there is NO workflow engine and NO node machinery):
  You, the human → 8 primary agents → 6 named sub-agents (specialists)

  Strategy:   video-strategy (manages audience-analyzer, competitor-analyzer,
              market-research-analyzer)
  Creative:   creative-director
  Story:      script-narrative
  Visual:     visual-design
  Production: scene-planning (manages shot-analyzer, clip-cutter,
              continuity-checker), asset-media
  Quality:    review-feedback
  Delivery:   delivery-export

Every primary agent has its own workspace, its own sessions, and is never
spawned as a subagent. The named sub-agents are specialists that a primary
agent may spawn by name via the `subagent` tool. The LLM is the agent — we
give it identity, capabilities, skills, and tools; HOW it works is entirely
its choice.

Created agents (WORKSPACE_REBUILD_PLAN W2) persist in data/agents/*.json
(gitignored) and are loaded at startup alongside the built-in 14 — the
registry is dynamic. A created agent immediately gets a workspace page,
sessions, and tool definitions from its chosen tools.

ALIASES maps the 17 pre-rebuild ids (WORKSPACE_REBUILD_PLAN W1) to their new
owners so historical data stays readable after the remap. The agents with no
mapping were retired: watcher-blocker became the internal law-watch
machinery, and recruiter was removed entirely."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

AGENTS: list[dict[str, Any]] = [
    {"id": "video-strategy", "department": "Strategy", "tier": "primary",
     "manages": ["audience-analyzer", "competitor-analyzer", "market-research-analyzer"],
     "identity": "I specialize in helping you define the big picture: goals, audience, "
                 "message, positioning, and strategic direction.",
     "capabilities": ["Market & Audience Insight", "Messaging & Positioning",
                      "Strategy & Planning", "Success Frameworks", "Competitive Analysis"],
     "skills": ["research", "positioning", "planning"], "tools": ["write_decision", "retrieve_knowledge"]},
    {"id": "creative-director", "department": "Creative", "tier": "primary", "manages": [],
     "identity": "I specialize in translating your strategy into a compelling concept, "
                 "tone, and emotional direction that stands out.",
     "capabilities": ["Concept Direction", "Visual Identity", "Tone & Style",
                      "Art Direction", "Storyboarding"],
     "skills": ["concept", "art direction"], "tools": ["write_decision", "retrieve_knowledge"]},
    {"id": "script-narrative", "department": "Story", "tier": "primary", "manages": [],
     "identity": "I specialize in turning your message into a clear, engaging story "
                 "with structure, pacing, and a voice your audience remembers.",
     "capabilities": ["Story Structure", "Script Writing", "Narrative Voice",
                      "Dialogue & Pacing", "Story Arc Design"],
     "skills": ["scripting", "knowledge-base retrieval"], "tools": ["retrieve_knowledge", "write_decision"]},
    {"id": "visual-design", "department": "Visual", "tier": "primary", "manages": [],
     "identity": "I specialize in defining the visual language — color, typography, "
                 "imagery, and motion — that makes your video unmistakably yours.",
     "capabilities": ["Visual Language", "Color & Typography", "Layout & Composition",
                      "Motion Design", "Brand Consistency"],
     "skills": ["visual design"], "tools": ["assign_visual", "write_decision"]},
    {"id": "scene-planning", "department": "Production", "tier": "primary",
     "manages": ["shot-analyzer", "clip-cutter", "continuity-checker"],
     "identity": "I specialize in breaking your story into scenes, shots, and sequences "
                 "— planning what happens on screen from start to finish.",
     "capabilities": ["Shot Planning", "Scene Sequencing", "Timing & Pacing",
                      "Camera Direction", "Continuity Planning"],
     "skills": ["shot planning"], "tools": ["assign_visual", "write_decision"]},
    {"id": "asset-media", "department": "Production", "tier": "primary", "manages": [],
     "identity": "I specialize in finding and organizing every asset you need — footage, "
                 "images, music, and references — ready for production.",
     "capabilities": ["Media Sourcing", "Asset Organization", "Licensing Checks",
                      "Media Cataloging", "Delivery Prep"],
     "skills": ["sourcing"], "tools": ["propose_source", "assign_visual", "write_decision"]},
    {"id": "review-feedback", "department": "Quality", "tier": "primary", "manages": [],
     "identity": "I specialize in reviewing work against your goals, gathering feedback, "
                 "and making sure the final video meets your standard.",
     "capabilities": ["Quality Review", "Fidelity Checking", "Feedback Synthesis",
                      "Revision Tracking", "Final Approval"],
     "skills": ["fidelity scoring"], "tools": ["score_fidelity", "write_decision"]},
    {"id": "delivery-export", "department": "Delivery", "tier": "primary", "manages": [],
     "identity": "I specialize in preparing your finished video for delivery — formats, "
                 "platforms, and final quality checks before release.",
     "capabilities": ["Export Planning", "Format Conversion", "Platform Delivery",
                      "Quality Control", "Release Packaging"],
     "skills": ["export planning", "editing"], "tools": ["tts_plan", "write_edit", "write_decision"]},
    # --- named sub-agents (spawnable by name via the subagent tool) -------
    {"id": "audience-analyzer", "department": "Strategy", "tier": "subagent",
     "parent": "video-strategy",
     "identity": "I'm the Audience Analyzer, a specialist on your video-strategy team. "
                 "I turn raw audience signals into personas, needs, and motivations.",
     "capabilities": ["Audience Analysis", "Persona Profiling"],
     "skills": ["research"], "tools": ["retrieve_knowledge"]},
    {"id": "competitor-analyzer", "department": "Strategy", "tier": "subagent",
     "parent": "video-strategy",
     "identity": "I'm the Competitor Analyzer, a specialist on your video-strategy team. "
                 "I map how competitors talk and where the openings are.",
     "capabilities": ["Competitor Analysis", "Benchmarking"],
     "skills": ["research"], "tools": ["retrieve_knowledge"]},
    {"id": "market-research-analyzer", "department": "Strategy", "tier": "subagent",
     "parent": "video-strategy",
     "identity": "I'm the Market Research Analyzer, a specialist on your video-strategy "
                 "team. I gather and synthesize market context for the strategy.",
     "capabilities": ["Market Research", "Trend Mapping"],
     "skills": ["research"], "tools": ["retrieve_knowledge"]},
    {"id": "shot-analyzer", "department": "Production", "tier": "subagent",
     "parent": "scene-planning",
     "identity": "I'm the Shot Analyzer, a specialist on your scene-planning team. "
                 "I dissect shots and reference footage into concrete plans.",
     "capabilities": ["Shot Analysis", "Composition Review"],
     "skills": ["analysis"], "tools": ["retrieve_knowledge"]},
    {"id": "clip-cutter", "department": "Production", "tier": "subagent",
     "parent": "scene-planning",
     "identity": "I'm the Clip Cutter, a specialist on your scene-planning team. "
                 "I select and prepare the footage for each shot.",
     "capabilities": ["Clip Sourcing", "Footage Selection"],
     "skills": ["sourcing"], "tools": ["retrieve_knowledge"]},
    {"id": "continuity-checker", "department": "Production", "tier": "subagent",
     "parent": "scene-planning",
     "identity": "I'm the Continuity Checker, a specialist on your scene-planning team. "
                 "I keep the plan consistent across scenes, shots, and versions.",
     "capabilities": ["Continuity Checking", "Error Detection"],
     "skills": ["consistency checking"], "tools": ["retrieve_knowledge"]},
]

BY_ID: dict[str, dict[str, Any]] = {a["id"]: a for a in AGENTS}

PRIMARY_IDS: list[str] = [a["id"] for a in AGENTS if a["tier"] == "primary"]
SUBAGENT_IDS: list[str] = [a["id"] for a in AGENTS if a["tier"] == "subagent"]

# --- dynamic registry: created agents persist on disk (W2) -----------------

CREATED_DIR = Path(__file__).resolve().parent.parent / "data" / "agents"

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_created(dir_path: Optional[Path] = None) -> list[dict[str, Any]]:
    """Created agent entries from data/agents/*.json. Corrupt or unknown
    entries are skipped — the built-in 14 are never touched. The directory
    is read from the CURRENT CREATED_DIR value (tests repoint it)."""
    if dir_path is None:
        dir_path = CREATED_DIR
    out: list[dict[str, Any]] = []
    if dir_path.is_dir():
        for path in sorted(dir_path.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(data, dict) and data.get("id") and \
                    data.get("tier") in ("primary", "subagent"):
                out.append(data)
    return out


CREATED: list[dict[str, Any]] = load_created()
ALL_AGENTS: list[dict[str, Any]] = AGENTS + CREATED


def _rebuild() -> None:
    global CREATED, ALL_AGENTS, BY_ID, PRIMARY_IDS, SUBAGENT_IDS
    CREATED = load_created()
    ALL_AGENTS = AGENTS + CREATED
    BY_ID = {a["id"]: a for a in ALL_AGENTS}
    PRIMARY_IDS = [a["id"] for a in ALL_AGENTS if a["tier"] == "primary"]
    SUBAGENT_IDS = [a["id"] for a in ALL_AGENTS if a["tier"] == "subagent"]


def slug_ok(slug: str) -> str | None:
    """Validate a slug for a NEW agent; returns an error message or None."""
    if not _SLUG_RE.match(slug):
        return "slug must be lowercase letters, digits, and dashes"
    if slug in BY_ID:
        return f"agent already exists: {slug}"
    if slug in ALIASES:
        return f"slug collides with a legacy alias: {slug}"
    return None


def create(entry: dict[str, Any], dir_path: Optional[Path] = None) -> str | None:
    """Persist a created agent entry and rebuild the dynamic registry.
    Returns an error message or None on success."""
    if dir_path is None:
        dir_path = CREATED_DIR
    err = slug_ok(str(entry.get("id", "")))
    if err:
        return err
    payload = dict(entry)
    payload["created"] = True
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / f"{payload['id']}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        return f"could not persist agent: {e}"
    _rebuild()
    return None

# pre-rebuild ids → their new owners (WORKSPACE_REBUILD_PLAN W1)
ALIASES: dict[str, str] = {
    "strategist": "video-strategy", "analyzer": "video-strategy",
    "planner": "script-narrative", "researcher": "asset-media",
    "audio-lead": "delivery-export", "tts": "delivery-export",
    "editor": "delivery-export", "graphics": "visual-design",
    "animation": "visual-design", "animated-graphics": "visual-design",
    "video-effects": "delivery-export", "clips": "scene-planning",
    "images": "asset-media", "reviewer": "review-feedback",
    "watcher-blocker": "review-feedback", "investigator": "review-feedback",
}


def resolve(agent_id: str) -> str:
    """Map a pre-rebuild id to its current owner; unknown ids pass through
    untouched (they are not ours to relabel)."""
    return ALIASES.get(agent_id, agent_id)
