"""Brain — the LLM layer. The only non-deterministic part of the system.

`converse()`            — plain conversational turns (the workspace chat voice):
                          streaming, ordinary model output, honest failure.
`converse_with_tools()` — the autonomous session voice (AUTONOMOUS_AGENTS_PLAN):
                          one model call that may return tool calls. The session
                          engine executes them; the runtime governs permissions,
                          laws, the steps cap, and the stop signal.

There is NO scripted voice anywhere. A missing or unreachable model is always
an honest state ("not configured" / "model unreachable") — nothing ever fakes
intelligence, in the workspace or anywhere else."""

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


class ModelUnreachable(RuntimeError):
    """The configured model could not be reached. The caller decides how to
    surface this honestly; no scripted impersonation ever replaces the model."""


# Test seam: a StubBrain set here replaces every brain path (deterministic
# runtime contract without a network model). Test-only — never production.
stub: Any = None


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


def _normalize_tool_calls(raw: Any) -> list[dict[str, Any]]:
    """Normalize provider tool_calls (OpenAI/Zhipu shape) into a stable list
    of {"name": str, "arguments": dict}."""
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for tc in raw:
        fn = tc.get("function") if isinstance(tc, dict) else None
        if not isinstance(fn, dict):
            continue
        name = str(fn.get("name") or "")
        if not name:
            continue
        args = fn.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except ValueError:
                args = {}
        if not isinstance(args, dict):
            args = {}
        out.append({"name": name, "arguments": args})
    return out


class LLMBrain:
    """Optional OpenAI/Azure/Zhipu-compatible client (chat completions).

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

    def converse(self, system: str, user: str) -> Iterator[str]:
        """The conversational voice. Ordinary model output only — never
        private chain-of-thought. A missing or failed model raises
        ModelUnreachable so the caller can surface the honest state."""
        if not (self.key and httpx):
            raise ModelUnreachable("no model configured")
        try:
            r = httpx.post(f"{self.base}/chat/completions",
                           headers={"Authorization": f"Bearer {self.key}"},
                           json={"model": self.model, "messages": [
                               {"role": "system", "content": system},
                               {"role": "user", "content": user}],
                               "stream": True, "max_tokens": 500}, timeout=45)
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
                content = delta.get("content") or ""
                if not content:
                    continue
                acc += content
                if acc.endswith((".", "!", "?", "\n")) and len(acc) > 2:
                    yield acc.strip()
                    acc = ""
            if acc.strip():
                yield acc.strip()
        except ModelUnreachable:
            raise
        except Exception as e:
            raise ModelUnreachable(f"model call failed: {type(e).__name__}") from e

    def converse_with_tools(self, system: str, user: str,
                            tool_defs: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        """The autonomous session voice: one call that may return tool calls.
        Returns (text, tool_calls) with tool_calls normalized to
        {"name", "arguments"}. A missing or failed model raises
        ModelUnreachable."""
        if not (self.key and httpx):
            raise ModelUnreachable("no model configured")
        try:
            body: dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 1000,
                "temperature": 0.3,
            }
            if tool_defs:
                body["tools"] = tool_defs
                body["tool_choice"] = "auto"
            r = httpx.post(f"{self.base}/chat/completions",
                           headers={"Authorization": f"Bearer {self.key}"},
                           json=body, timeout=60)
            r.raise_for_status()
            data = r.json()
            message = (data.get("choices") or [{}])[0].get("message", {})
            text = str(message.get("content") or "")
            calls = _normalize_tool_calls(message.get("tool_calls"))
            return text, calls
        except ModelUnreachable:
            raise
        except Exception as e:
            raise ModelUnreachable(f"model call failed: {type(e).__name__}") from e


class StubBrain:
    """Test double — deterministic, test-only, never a production voice.

    Scriptable: a queue of steps, each either a text reply or a list of tool
    calls. `converse_with_tools` consumes one step per call, so tests can
    drive whole autonomous sessions (spawns, handoffs, capability creation,
    steps caps) without a network model. `converse` consumes only text steps
    and yields "" for tool steps (plain conversational turns don't execute
    tools)."""

    def __init__(self) -> None:
        self.steps: list[tuple[str, Any]] = []
        self.calls: list[dict[str, Any]] = []
        self.fail = False

    def add_text(self, text: str) -> "StubBrain":
        self.steps.append(("text", text))
        return self

    def add_tools(self, calls: list[dict[str, Any]]) -> "StubBrain":
        """calls: list of {"name": str, "arguments": dict}."""
        self.steps.append(("tools", calls))
        return self

    def _next(self) -> tuple[str, Any]:
        if self.steps:
            return self.steps.pop(0)
        return ("text", "I understand. Let's talk it through.")

    def converse(self, system: str, user: str) -> Iterator[str]:
        self.calls.append({"system": system, "user": user, "tools": []})
        if self.fail:
            raise ModelUnreachable("stub failure")
        if not self.steps or self.steps[0][0] == "text":
            kind, value = self._next()
            if kind == "text":
                yield value
        else:
            yield ""

    def converse_with_tools(self, system: str, user: str,
                            tool_defs: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        self.calls.append({"system": system, "user": user,
                           "tools": [d.get("name", "") for d in tool_defs]})
        if self.fail:
            raise ModelUnreachable("stub failure")
        kind, value = self._next()
        if kind == "text":
            return value, []
        return "", value

    def model_configured(self) -> bool:
        return True


def get_brain() -> Any:
    if stub is not None:
        return stub
    return LLMBrain()


def model_configured() -> bool:
    """True when the conversational layer can genuinely speak: a test stub is
    in place, or a key and an HTTP client exist. Never fakes availability."""
    if stub is not None:
        return True
    return bool(_key()) and httpx is not None