"""Knowledge repository — the system's memory across runs.

After every run the final state is persisted to `runs/<run-id>/`:
  knowledge.json — flat corpus entries (decisions, edits, review verdicts,
                   revocations) for retrieval
  state.json     — full state snapshot, for audit

`retrieve()` is a deterministic BM25-style keyword retrieval over that corpus:
the same query + corpus always yields the same ranking, and every fact comes
from a recorded run — nothing is invented (Law 1). This is the RAG layer that
planner uses to ground its script on the system's own past decisions."""

from __future__ import annotations

import json
import math
import os
import re
import time
from collections import Counter
from typing import Any, Optional

RUNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "runs")

_K1 = 1.5
_B = 0.75


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"\W+", (text or "").lower()) if len(t) > 2]


def _run_dir(run_id: str) -> str:
    return os.path.join(RUNS_DIR, run_id)


def list_runs() -> list[str]:
    if not os.path.isdir(RUNS_DIR):
        return []
    return sorted(d for d in os.listdir(RUNS_DIR)
                  if os.path.isdir(os.path.join(RUNS_DIR, d)))


def record_run(state: dict[str, Any], run_id: Optional[str] = None) -> str:
    """Persist the final state of a run into the knowledge repository.
    Returns the run id. Pure stdlib; never raises (best-effort storage)."""
    run_id = run_id or time.strftime("run-%Y%m%d-%H%M%S")
    try:
        os.makedirs(_run_dir(run_id), exist_ok=True)
        entries: list[dict[str, Any]] = []
        for d in state.get("decisions", []):
            entries.append({"kind": "decision", "agent": d.get("agent", "?"),
                            "text": d.get("text", "")})
        for e in state.get("edits", []):
            entries.append({"kind": "edit", "agent": e.get("agent", "?"),
                            "text": f"{e.get('file', '')}: {e.get('change', '')}"})
        report = state.get("review_report") or {}
        if report.get("decision"):
            entries.append({"kind": "review", "agent": "reviewer",
                            "text": f"fidelity {report['decision']}: "
                                    f"{json.dumps(report.get('checks', {}))}"})
        for r in state.get("revocations", []):
            entries.append({"kind": "revocation", "agent": r.get("agent", "?"),
                            "text": f"Law {r.get('law', '?')} {r.get('law_name', '')}: "
                                    f"{r.get('reason', '')}"})
        with open(os.path.join(_run_dir(run_id), "knowledge.json"), "w") as f:
            json.dump({"run_id": run_id, "topic": state.get("topic"),
                       "entries": entries}, f, indent=2)
        with open(os.path.join(_run_dir(run_id), "state.json"), "w") as f:
            json.dump({k: v for k, v in state.items()
                       if k not in ("log", "mailboxes")}, f, indent=2, default=str)
    except OSError:
        pass
    return run_id


def load_corpus() -> list[dict[str, Any]]:
    """All knowledge entries across every recorded run, newest runs first."""
    out: list[dict[str, Any]] = []
    for run_id in reversed(list_runs()):
        path = os.path.join(_run_dir(run_id), "knowledge.json")
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        for e in data.get("entries", []):
            e = dict(e)
            e["run"] = run_id
            e.setdefault("text", "")
            out.append(e)
    return out


def retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """BM25 keyword retrieval over the persisted corpus. Deterministic: the
    same corpus + query always returns the same ranked list."""
    docs = load_corpus()
    if not docs or not query:
        return []
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    doc_tokens = [_tokenize(d.get("text", "")) for d in docs]
    n = len(docs)
    df: dict[str, int] = {}
    for toks in doc_tokens:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) for t in q_tokens if t in df}

    avgdl = sum(len(t) for t in doc_tokens) / max(n, 1)
    scored: list[tuple[float, int]] = []
    for i, toks in enumerate(doc_tokens):
        counts = Counter(toks)
        dl = len(toks)
        s = 0.0
        for t in q_tokens:
            tf = counts.get(t, 0)
            if not tf or t not in idf:
                continue
            denom = tf + _K1 * (1 - _B + _B * dl / max(avgdl, 1))
            s += idf[t] * tf * (_K1 + 1) / denom
        if s > 0:
            scored.append((s, i))
    scored.sort(key=lambda x: -x[0])
    return [{**docs[i], "score": round(s, 4)} for s, i in scored[:top_k]]