"""UI 1 — opencode-style streaming console.

Prints everything the system does, exactly as it happens: agent thinking,
tool calls and results, law checks, watchpoint scans, routes, and CEO
approval prompts. ANSI colors; safe when piped (colors auto-off)."""

from __future__ import annotations

import sys
from typing import Any

import avis.events as events
from avis.laws import describe

COLOR = {
    "note": "\033[36m",      # cyan
    "thinking": "\033[90m",  # dim gray
    "tool_call": "\033[33m",  # yellow
    "tool_result": "\033[37m",  # white
    "law_block": "\033[31m",  # red
    "route": "\033[35m",     # magenta
    "interrupt": "\033[1;34m",  # bold blue
    "result": "\033[32m",    # green
    "reset": "\033[0m",
}


class Console:
    def __init__(self, use_color: bool | None = None) -> None:
        self.use_color = sys.stdout.isatty() if use_color is None else use_color

    def listen(self, ev: dict[str, Any]) -> None:
        kind, agent, text = ev["kind"], ev["agent"], ev.get("text", "")
        c = COLOR.get(kind, "")
        tag = f"{agent:<16}"
        prefix = {"note": "·", "thinking": "…", "tool_call": "→", "tool_result": "←",
                  "law_block": "✗", "route": "►", "interrupt": "?", "result": "✓"}.get(kind, " ")
        line = f"{prefix} {tag} {text}"
        if self.use_color:
            line = f"{c}{line}\033[0m"
        print(line, flush=True)

    def banner(self, mermaid: str = "") -> None:
        print("\n" + "=" * 70)
        print("  AGENTIC VIDEO SYSTEM — LangGraph runtime")
        print("  17 agents · 5 departments · 12 laws · deterministic orchestrator")
        print("=" * 70)
        print("THE 12 LAWS (enforced at every step):")
        print(describe())
        if mermaid:
            print("\nNOTE: run `uvicorn ui.web.server:app` for the graph view UI.")

    def show_final(self, state: dict[str, Any]) -> None:
        print("\n" + "=" * 70)
        print("  FINAL STATE SUMMARY")
        print("=" * 70)
        report = state.get("review_report") or {}
        print(f"  review decision : {report.get('decision')}")
        print(f"  checks          : {report.get('checks')}")
        print(f"  iterations      : {state.get('iterations')}")
        print(f"  revocations     : {len(state.get('revocations', []))}")
        print(f"  decisions       : {len(state.get('decisions', []))}")
        print(f"  visual assigns  : {len(state.get('visual_assignments', []))}")
        tts = state.get("voice_track") or {}
        print(f"  tts segments    : {len(tts.get('segments', []))} ({tts.get('engine')})")
        print("=" * 70)


def approvals(question: dict[str, Any]) -> Any:
    """Default CEO: prompts on stdin. 'yes/y' approves, anything else rejects."""
    q = question.get("question", "Approve?")
    if "script" in question:
        print(f"\n--- SCRIPT DRAFT ---\n{question['script']}\n--------------------\n")
    if "proposals" in question:
        print(f"\n--- PROPOSED SOURCES ({len(question['proposals'])}) ---")
        for i, p in enumerate(question["proposals"]):
            print(f"  [{i}] {p.get('kind')}: {p.get('description')} ({p.get('url')})")
        print("----------------------\n")
    answer = input(f"{q} (y/n): ").strip().lower()
    return "approve" if answer in ("y", "yes", "approve") else f"rejected: {answer}"


def main() -> None:
    import argparse

    from avis.graph import build_graph, run, seed_state

    ap = argparse.ArgumentParser(description="Agentic Video System console UI")
    ap.add_argument("--topic", default="Why Mbappé shines on the biggest stage", help="video topic")
    ap.add_argument("--reference-analysis", default=None, help="path to reference-analysis JSON")
    ap.add_argument("--yes", action="store_true", help="auto-approve all CEO prompts")
    ap.add_argument("--list-agents", action="store_true")
    args = ap.parse_args()

    if args.list_agents:
        from avis.agents import AGENTS
        for a in AGENTS:
            print(f"  {a['id']:<18} {a['department']:<10} {a['tier']}")
        return

    console = Console()
    graph, mermaid = build_graph()
    console.banner(mermaid)
    events.bus.subscribe(console.listen)
    state = seed_state(args.topic, reference_file=args.reference_analysis)
    approver = (lambda q: "approve") if args.yes else approvals
    final = run(graph, state, approver)
    console.show_final(final)


if __name__ == "__main__":
    main()