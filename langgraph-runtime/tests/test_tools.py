"""Tool registry — deterministic behavior of the knowledge/RAG tools and the
fidelity scorer."""

from __future__ import annotations

import json

import avis.knowledge as knowledge
from avis import tools


def _state(**kw):
    s = {"decisions": [], "edits": [], "mailboxes": {}, "revocations": [],
         "visual_assignments": [], "sourcing_proposals": [], "voice_profile": {},
         "asset_bundle": {"assets": []}}
    s.update(kw)
    return s


def test_write_decision_and_retrieve_memory() -> None:
    state = _state()
    tools.call(state, "video-strategy", "write_decision",
               {"agent": "video-strategy", "text": "run plan locked on long-form"},
               "build")
    result = tools.call(state, "script-narrative", "retrieve_memory",
                        {"query": "run plan"}, "plan")
    assert result["retrieved"] and "run plan locked" in result["retrieved"][0]["text"]


def test_read_state_fails_loudly_on_missing() -> None:
    result = tools.call(_state(), "asset-media", "read_state",
                        {"fields": ["blueprint"]}, "plan")
    assert "error" in result and "Law 12" in result["error"]


def test_retrieve_knowledge_cross_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    knowledge.record_run({"topic": "t1", "decisions": [
        {"agent": "video-strategy", "text": "asset bundle confirmed for Mbappé film"}]},
        run_id="run-0001")
    knowledge.record_run({"topic": "t2", "decisions": [
        {"agent": "script-narrative", "text": "script approved for tennis film"}]},
        run_id="run-0002")

    hits = knowledge.retrieve("asset bundle")
    assert len(hits) == 1 and hits[0]["run"] == "run-0001"

    hits = knowledge.retrieve("script approved")
    assert len(hits) == 1 and hits[0]["run"] == "run-0002"

    assert knowledge.retrieve("") == []
    assert knowledge.retrieve("zzz no match") == []


def test_record_run_isolates_state(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    knowledge.record_run({"topic": "t", "revocations": [
        {"agent": "delivery-export", "law": 6, "law_name": "No Effect Substitution",
         "reason": "effect outside vocabulary"}]}, run_id="run-0001")
    entries = knowledge.load_corpus()
    kinds = {e["kind"] for e in entries}
    assert "revocation" in kinds and "review" not in kinds


def test_propose_source_requires_verification_flag() -> None:
    state = _state()
    r = tools.call(state, "asset-media", "propose_source",
                   {"kind": "videoclip", "description": "candidates",
                    "url": "https://src", "license_tbd": True,
                    "content_verified": False}, "build")
    p = r["sourcing_proposals"][0]
    assert p["license"] == "NOT_VERIFIED" and p["content_verified"] is False


def test_assign_visual_carries_image_ref() -> None:
    state = _state()
    r = tools.call(state, "visual-design", "assign_visual",
                   {"agent": "visual-design", "segment": "hook", "asset_id": "src-1",
                    "kind": "visual-design", "image_ref": "src-1-overlay.png"}, "build")
    a = r["visual_assignments"][0]
    assert a["image_ref"] == "src-1-overlay.png"

    r = tools.call(state, "scene-planning", "assign_visual",
                   {"agent": "scene-planning", "segment": "hook",
                    "asset_id": "src-1", "kind": "scene-planning"}, "build")
    assert "image_ref" not in r["visual_assignments"][0]


def test_score_fidelity_passes_happy_path() -> None:
    blueprint = {"segments": [{"name": f"s{i}"} for i in range(3)],
                 "target_duration_s": 60}
    bundle = {"assets": [{"id": "src-1"}, {"id": "src-2"}, {"id": "src-3"}]}
    spec = {"shots": [{"segment": f"s{i}", "asset_id": f"src-{i+1}"} for i in range(3)],
            "estimated_duration_s": 60}
    tts = {"segments": [{"segment": i} for i in range(3)]}
    assignments = [{"kind": "graphics", "segment": f"s{i}", "asset_id": f"src-{i+1}",
                    "image_ref": "x.png"} for i in range(3)]

    r = tools.call(_state(blueprint=blueprint, asset_bundle=bundle, cut_spec=spec,
                          voice_track=tts, visual_assignments=assignments),
                   "review-feedback", "score_fidelity", {}, "plan")
    report = r["review_report"]
    assert report["decision"] == "pass"
    assert all(report["checks"].values())


def test_score_fidelity_flags_missing_asset() -> None:
    blueprint = {"segments": [{"name": "s0"}], "target_duration_s": 60}
    spec = {"shots": [{"segment": "s0", "asset_id": "src-99"}], "estimated_duration_s": 60}
    r = tools.call(_state(blueprint=blueprint, asset_bundle={"assets": []},
                          cut_spec=spec, voice_track={"segments": [{"segment": 0}]}),
                   "review-feedback", "score_fidelity", {}, "plan")
    report = r["review_report"]
    assert report["decision"] == "revise" and report["missing_assets"] == ["src-99"]


def test_tts_plan_rejects_unauthorized_engine_switch() -> None:
    state = _state(voice_profile={"default_engine": "coqui_xtts_v2", "authorized_engines": []})
    r = tools.call(state, "delivery-export", "tts_plan",
                   {"engine": "piper", "voice_sample": "voice.wav"}, "build")
    assert "error" in r and "Law 7" in r["error"]