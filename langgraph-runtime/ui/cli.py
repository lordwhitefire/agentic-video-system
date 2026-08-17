"""UI 1 — terminal console over the new session engine.

Prints everything the runtime does, exactly as it happens: agent reasoning,
tool calls and results, law checks, approvals. Then an interactive REPL:
talk to one primary agent through the same session engine the web UI uses
(one human message = one session turn). ANSI colors; safe when piped."""

from __future__ import annotations

import sys
from typing import Any

import avis.events as events
import avis.studio as studio
from avis.brain import model_configured
from avis.laws import describe

COLOR = {
    "note": "\033[36m",      # cyan
    "thinking": "\033[90m",  # dim gray
    "tool_call": "\033[33m",  # yellow
    "tool_result": "\033[37m",  # white
    "law_block": "\033[31m",  # red
    "approval_request": "\033[1;34m",  # bold blue
    "error": "\033[31m",     # red
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
                  "law_block": "✗", "approval_request": "?", "error": "!"}.get(kind, " ")
        line = f"{prefix} {tag} {text}"
        if self.use_color:
            line = f"{c}{line}\033[0m"
        print(line)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Agentic Video System console")
    ap.add_argument("--agent", default="video-strategy",
                    help="which primary agent to talk to")
    ap.add_argument("--mode", default="plan", choices=["plan", "build"])
    ap.add_argument("--list-agents", action="store_true")
    args = ap.parse_args()

    if args.list_agents:
        for a in studio.registry():
            print(f"  {a['id']:<18} {a['department']:<10} {a['tier']}")
        return

    if args.agent not in studio.NAMES:
        print(f"unknown agent: {args.agent}")
        return

    print("=" * 70)
    print(f"  {studio.NAMES[args.agent]} — {studio.DESCRIPTIONS[args.agent]}")
    print("  the 12 laws:")
    print(describe())
    print("=" * 70)

    events.bus.subscribe(Console().listen)
    if not model_configured():
        print("note: no model key configured — sessions will surface that "
              "honestly (no scripted replies).")

    session = studio.new_session(args.agent, "console session", mode=args.mode)
    while True:
        try:
            message = input(f"\nyou ({args.mode}): ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not message:
            continue
        if message in ("exit", "quit"):
            break
        if message == "build":
            session["mode"] = "build"
            args.mode = "build"
            print("-> build mode")
            continue
        if message == "plan":
            session["mode"] = "plan"
            args.mode = "plan"
            print("-> plan mode")
            continue
        session["conversation"].append(
            {"type": "user_message", "agent_id": "you",
             "timestamp": studio._iso(), "content": message})
        session["status"] = "working"
        outcome = studio.run_session(
            args.agent, session["id"], message, session["state"],
            session["mode"], session=session,
            should_stop=lambda: False)
        print(f"\n[{outcome.get('status')}]")


if __name__ == "__main__":
    main()