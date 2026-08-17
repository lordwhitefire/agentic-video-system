"""Event bus. Every runtime event (thinking, tool calls, law checks, routes)
flows through here so the UIs (streaming console, web graph view) can observe
the system live. The orchestrator itself is deterministic; events are pure
observability."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

Listener = Callable[[dict[str, Any]], None]


class _Bus:
    def __init__(self) -> None:
        self._listeners: list[Listener] = []
        self._lock = threading.Lock()
        self._history: list[dict[str, Any]] = []

    def subscribe(self, listener: Listener) -> None:
        with self._lock:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Listener) -> None:
        with self._lock:
            self._listeners.remove(listener)

    def emit(self, agent: str, kind: str, text: str = "", **data: Any) -> None:
        with self._lock:
            ev = {"ts": time.time(), "agent": agent, "kind": kind, "text": text, **data}
            self._history.append(ev)
            listeners = list(self._listeners)
        for ln in listeners:
            try:
                ln(ev)
            except Exception:
                pass

    def history(self, since: float = 0.0) -> list[dict[str, Any]]:
        with self._lock:
            return [e for e in self._history if e["ts"] >= since]

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get the most recent events (for notifications)."""
        with self._lock:
            return self._history[-limit:]


bus = _Bus()