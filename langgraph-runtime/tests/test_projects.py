"""W3/W4 — projects (real scopes) and resources (real files).

The backend project store starts EMPTY — the front-end mock project list is
the seed (decision 9). Real projects append via the selector; real uploads
land on disk and merge into the same categories in the UI.

Exact reply text is never asserted (test doubles only).
"""

from __future__ import annotations

import os
import time
from pathlib import Path

os.environ["AVIS_LLM_ENABLED"] = "0"

import pytest
from fastapi.testclient import TestClient

import avis.brain as brain
from avis import events
from avis import knowledge
from avis import studio
from avis import tools
from ui.web import server


@pytest.fixture(autouse=True)
def _stub_brain(monkeypatch):
    stub = brain.StubBrain()
    monkeypatch.setattr(brain, "stub", stub)
    return stub


@pytest.fixture(autouse=True)
def _isolate_knowledge(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    yield


@pytest.fixture(autouse=True)
def _isolate_bus(monkeypatch):
    from avis.events import _Bus
    monkeypatch.setattr(events, "bus", _Bus())
    yield


@pytest.fixture(autouse=True)
def _isolate_workspace_store(monkeypatch):
    monkeypatch.setattr(studio, "WORKSPACES", {})
    yield


@pytest.fixture(autouse=True)
def _isolate_capabilities(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "CAPABILITIES_DIR", Path(tmp_path) / "capabilities")
    yield


@pytest.fixture(autouse=True)
def _isolate_projects(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, "PROJECTS_DIR", Path(tmp_path) / "projects")
    yield


@pytest.fixture()
def client():
    with TestClient(server.app) as c:
        yield c


def test_projects_start_empty_and_create(client) -> None:
    assert client.get("/api/projects").json()["projects"] == []
    r = client.post("/api/projects", json={"name": "Q3 Launch Film"})
    assert r.json()["ok"] is True
    summary = r.json()["project"]
    assert summary["id"] == "q3-launch-film"
    assert summary["name"] == "Q3 Launch Film"
    assert summary["resources"]["Media Library"] == []
    projects = client.get("/api/projects").json()["projects"]
    assert [p["id"] for p in projects] == ["q3-launch-film"]


def test_create_project_validation(client) -> None:
    assert client.post("/api/projects", json={}).json()["ok"] is False
    client.post("/api/projects", json={"name": "Q3 Launch Film"})
    dup = client.post("/api/projects", json={"name": "q3-launch-film"})
    assert dup.json()["ok"] is False
    assert "already exists" in dup.json()["error"]


def test_resource_upload_roundtrip(client) -> None:
    client.post("/api/projects", json={"name": "Q3 Launch Film"})
    r = client.post(
        "/api/projects/q3-launch-film/resources",
        files={"file": ("brand-guidelines.pdf", b"%PDF-1.7 fake content", "application/pdf")},
        data={"category": "Brand Kit"},
    )
    assert r.json()["ok"] is True
    assert r.json()["name"] == "brand-guidelines.pdf"

    res = client.get("/api/projects/q3-launch-film/resources").json()["resources"]
    assert [f["name"] for f in res["Brand Kit"]] == ["brand-guidelines.pdf"]
    record = res["Brand Kit"][0]
    assert record["size"] == len(b"%PDF-1.7 fake content")
    assert record["type"] == "pdf"
    assert res["Knowledge Base"] == []

    got = client.get(
        "/api/projects/q3-launch-film/resources/Brand%20Kit/brand-guidelines.pdf")
    assert got.status_code == 200
    assert got.content == b"%PDF-1.7 fake content"


def test_resource_validation(client) -> None:
    assert client.get("/api/projects/nope/resources").status_code == 404
    client.post("/api/projects", json={"name": "Q3 Launch Film"})
    bad = client.post(
        "/api/projects/q3-launch-film/resources",
        files={"file": ("a.txt", b"x", "text/plain")},
        data={"category": "Nonsense"},
    )
    assert bad.json()["ok"] is False
    assert "unknown category" in bad.json()["error"]
    missing = client.get(
        "/api/projects/q3-launch-film/resources/Brand%20Kit/ghost.pdf")
    assert missing.status_code == 404


def test_session_tagged_with_project(client, _stub_brain, monkeypatch) -> None:
    client.post("/api/projects", json={"name": "Q3 Launch Film"})
    client.post(
        "/api/projects/q3-launch-film/resources",
        files={"file": ("lookbook.pdf", b"%PDF lookbook", "application/pdf")},
        data={"category": "References"},
    )
    seen: list[str] = []
    original = studio._Engine._build_user_prompt

    def spy(self):
        seen.append(self._build_user_prompt.__self__ is self)
        return original(self)

    monkeypatch.setattr(studio._Engine, "_build_user_prompt", spy)
    _stub_brain.add_text("Plan complete.")
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "Plan the Q3 launch film.",
                          "project": "q3-launch-film"})
    assert r.json()["ok"] is True

    def done(snap):
        sess = snap["active_session"]
        return bool(sess and sess["status"] == "idle")

    deadline = time.time() + 20
    while time.time() < deadline:
        snap = client.get("/api/studio/agents/video-strategy").json()
        if done(snap):
            break
        time.sleep(0.05)
    else:
        pytest.fail("timed out waiting for the session")

    assert snap["active_session"]["project"] == "q3-launch-film"
    assert seen, "the engine built a user prompt"
    sess = {"id": "s1", "title": "t", "status": "idle", "mode": "plan",
            "task": "t", "conversation": [], "project": "q3-launch-film",
            "state": {"memory": {}}}
    prompt = original(studio._Engine("video-strategy", sess, "t", {}, "plan"))
    assert "active project: Q3 Launch Film" in prompt
    assert "lookbook.pdf" in prompt


def test_unknown_project_rejected_on_messages(client) -> None:
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "hello", "project": "no-such-project"})
    assert r.json()["ok"] is False
    assert "unknown project" in r.json()["error"]


def test_projects_survive_reload(client) -> None:
    client.post("/api/projects", json={"name": "Q3 Launch Film"})
    client.post(
        "/api/projects/q3-launch-film/resources",
        files={"file": ("cut.mp4", b"mp4fake", "video/mp4")},
        data={"category": "Media Library"},
    )
    assert studio.get_project("q3-launch-film") is not None
    res = studio.list_resources("q3-launch-film")
    assert [f["name"] for f in res["Media Library"]] == ["cut.mp4"]
