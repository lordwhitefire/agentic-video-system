"""Brain — the only non-deterministic layer, and it is optional.

With an LLM key (OPENAI_API_KEY or AZURE_OPENAI_API_KEY) in the environment,
agents stream real reasoning. Without one, the scripted brain emits
deterministic "thinking" lines that restate only facts present in state —
exactly what Law 1 permits (never invention).

The pipeline runs identically in both modes: the orchestrator, laws, tools,
and approval gates never depend on the LLM."""

from __future__ import annotations

import json
import os
from typing import Any, Iterator, Optional

import avis.events as events

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None

ZHIPU_BASE = "https://open.bigmodel.cn/api/paas/v4"
ZHIPU_DEFAULT_MODEL = "glm-4.5-flash"
DEFAULT_MODEL = "gpt-4o-mini"


def _load_dotenv() -> None:
    """Minimal .env loader for langgraph-runtime/.env (KEY=VALUE lines).
    Never overrides variables already set in the environment. The file stays
    gitignored — keys are never committed."""
    path = os.path.join(os.path.dirname(__file__), "..", ".env")
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


def _key() -> Optional[str]:
    _load_dotenv()
    return (os.environ.get("OPENAI_API_KEY")
            or os.environ.get("AZURE_OPENAI_API_KEY")
            or os.environ.get("GLM_API_KEY"))


class ScriptedBrain:
    """Deterministic fallback. Produces thinking lines strictly from state facts."""

    def think(self, agent_id: str, ctx: dict[str, Any]) -> Iterator[str]:
        topic = ctx.get("topic") or "the topic"
        has_blueprint = bool(ctx.get("blueprint"))
        segments = (ctx.get("blueprint") or {}).get("segments") or []
        yield f"I am {agent_id}. Task received; state has topic='{topic}', blueprint={'yes' if has_blueprint else 'no'}."
        if segments:
            count = len(segments) if isinstance(segments, list) else segments.get("count", "?")
            yield f"Blueprint supplies a {count}-part structural template; I work strictly inside it (Laws 1, 6)."
        missing = ctx.get("_missing", [])
        if missing:
            yield f"Required inputs not present: {', '.join(missing)}. I stop and ask rather than guess (Law 1)."
        else:
            yield "All required inputs are present in state. Proceeding with the deterministic step for this node."


class LLMBrain:
    """Optional OpenAI/Azure/Zhipu-compatible client (chat completions only).

    Provider selection, in priority order:
      1. OPENAI_BASE_URL set  -> use it (any OpenAI-compatible endpoint)
      2. GLM_API_KEY set      -> Zhipu BigModel (https://open.bigmodel.cn/api/paas/v4)
      3. otherwise            -> api.openai.com
    Model: AVIS_LLM_MODEL env var overrides the per-provider default."""

    def __init__(self) -> None:
        _load_dotenv()
        self.key = _key()
        base = os.environ.get("OPENAI_BASE_URL")
        if base:
            self.base = base
            self.model = os.environ.get("AVIS_LLM_MODEL", DEFAULT_MODEL)
        elif os.environ.get("GLM_API_KEY"):
            self.base = ZHIPU_BASE
            self.model = os.environ.get("AVIS_LLM_MODEL", ZHIPU_DEFAULT_MODEL)
        else:
            self.base = "https://api.openai.com/v1"
            self.model = os.environ.get("AVIS_LLM_MODEL", DEFAULT_MODEL)

    def think(self, agent_id: str, ctx: dict[str, Any]) -> Iterator[str]:
        if not (self.key and httpx):
            yield from ScriptedBrain().think(agent_id, ctx)
            return
        if os.environ.get("AVIS_LLM_ENABLED", "1") == "0":
            yield from ScriptedBrain().think(agent_id, ctx)
            return
        system = ("You are an agent in a deterministic video-editing orchestrator. "
                  "Speak in short, concrete thinking lines. Never invent facts; "
                  "only reason from what is in the context. If input is missing, say so and stop.")
        prompt = json.dumps({"agent": agent_id, "context": {k: v for k, v in ctx.items() if k in (
            "topic", "blueprint", "script", "manifest", "asset_bundle", "cut_spec", "review_report", "pending_input")}})
        try:
            r = httpx.post(f"{self.base}/chat/completions",
                           headers={"Authorization": f"Bearer {self.key}"},
                           json={"model": self.model, "messages": [
                               {"role": "system", "content": system},
                               {"role": "user", "content": prompt}],
                               "stream": True, "max_tokens": 120}, timeout=30)
            r.raise_for_status()
            acc = ""
            for line in r.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    delta = json.loads(data)["choices"][0].get("delta", {})
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                content = delta.get("content") or delta.get("reasoning_content") or ""
                if not content:
                    continue
                acc += content
                if acc.endswith((".", "!", "?", "\n")) and len(acc) > 2:
                    yield acc.strip()
                    acc = ""
            if acc.strip():
                yield acc.strip()
        except Exception:
            yield "LLM unreachable — falling back to deterministic scripted thinking (no inference, per Law 1)."
            yield from ScriptedBrain().think(agent_id, ctx)


def get_brain() -> Any:
    return LLMBrain() if _key() else ScriptedBrain()


def think_stream(agent_id: str, ctx: dict[str, Any]) -> None:
    """Emit a node's reasoning to the bus, line by line, as it happens."""
    brain = get_brain()
    for line in brain.think(agent_id, ctx):
        events.bus.emit(agent_id, "thinking", line)