"""The 12 laws — every guard must fire on violation and stay silent on clean actions."""

from __future__ import annotations

import pytest

from avis.laws import BY_ID, LAWS, describe, guard


def test_twelve_laws_registered() -> None:
    assert len(LAWS) == 12
    assert set(BY_ID) == set(range(1, 13))


def test_clean_action_no_revocation() -> None:
    state = {"substitutions": []}
    record = guard(state, "graphics", {"guessy": False})
    assert record == {}


@pytest.mark.parametrize("key", [
    "guessy", "unproven", "effect_off_blueprint", "engine_switch",
    "graphic_without_image", "reused_image", "watermarked",
    "runtime_swap", "assuming_context", "carry_over",
])
def test_flag_keys_block(key: str) -> None:
    record = guard({}, "agent", {key: True})
    assert record and record["blocked"] is True
    assert record["law"] >= 1 and record["law"] <= 12


def test_law3_substitution_requires_approval() -> None:
    state = {"substitutions": []}
    record = guard(state, "clips", {"substitution": True, "substitution_id": "src-1"})
    assert record and record["law"] == 3

    approved = {"substitutions": [{"id": "src-1"}]}
    assert guard(approved, "clips", {"substitution": True, "substitution_id": "src-1"}) == {}


def test_law4_auto_correction_blocked() -> None:
    record = guard({}, "editor", {"auto_correct": {"authorized": False}})
    assert record and record["law"] == 4


def test_describe_mentions_law_names() -> None:
    text = describe()
    assert "No Inference" in text and "No Assuming Context" in text