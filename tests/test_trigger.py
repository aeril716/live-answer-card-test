"""Offline tests for trigger.should_fire() — no network, no real model.

The accuracy oracle is context/trigger_labelled_set.json: one simulated call,
in order, shared call state. Swap that file to change the canonical set.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import model_client
import trigger

ORACLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "context", "trigger_labelled_set.json")

with open(ORACLE_PATH, encoding="utf-8") as f:
    LABELLED = [tuple(row) for row in json.load(f)]


@pytest.fixture(autouse=True)
def fresh_call(monkeypatch):
    monkeypatch.setattr(trigger, "USE_MOCK", True)
    monkeypatch.setattr(trigger, "USE_MEM0", False)
    calls = []
    monkeypatch.setattr(model_client, "fast_complete",
                        lambda *a, **k: calls.append(a) or "")
    trigger.reset_call()
    yield calls
    trigger.reset_call()


def _run_oracle():
    results = []
    ts = 0.0
    for text, speaker, _, _ in LABELLED:
        ts += 1.0
        results.append(trigger.should_fire({"text": text, "speaker": speaker, "ts": ts}))
    return results


def test_oracle_accuracy_18_of_20(fresh_call):
    results = _run_oracle()
    correct = sum(1 for (t, s, exp_fire, exp_reason), r in zip(LABELLED, results)
                  if r["fire"] == exp_fire and r["reason"] == exp_reason)
    wrong = [(t, r["fire"], r["reason"]) for (t, s, ef, er), r in zip(LABELLED, results)
             if not (r["fire"] == ef and r["reason"] == er)]
    assert correct >= 18, f"{correct}/20 correct; wrong: {wrong}"


def test_hard_gate_zero_smalltalk_fires(fresh_call):
    results = _run_oracle()
    fired_smalltalk = [t for (t, s, ef, er), r in zip(LABELLED, results)
                       if er == "smalltalk" and r["fire"]]
    assert fired_smalltalk == [], f"small talk fired: {fired_smalltalk}"


def test_no_model_calls_in_mock_mode(fresh_call):
    _run_oracle()
    assert fresh_call == [], "mock mode must never call the model"


def test_fired_technical_questions_keep_product_names(fresh_call):
    results = _run_oracle()
    by_text = {t: r for (t, s, ef, er), r in zip(LABELLED, results)}
    gw = by_text["Wait, what about Gateway — how long does it keep logs?"]
    assert gw["fire"] and "gateway" in gw["question"].lower()


def test_repeat_resets_between_calls(fresh_call):
    q = {"text": "Are you SOC 2 certified?", "speaker": "prospect", "ts": 1.0}
    assert trigger.should_fire(q)["fire"] is True
    again = trigger.should_fire({**q, "text": "Are you SOC 2 compliant?"})
    assert again == {"fire": False, "question": "", "reason": "repeat"}
    trigger.reset_call()
    assert trigger.should_fire(q)["fire"] is True


def test_rep_speech_never_fires_and_makes_no_model_call(fresh_call):
    r = trigger.should_fire({"text": "Does our Gateway support failover?",
                             "speaker": "rep", "ts": 1.0})
    assert r == {"fire": False, "question": "", "reason": "not_a_question"}
    assert fresh_call == []


def test_never_raises_on_garbage(fresh_call):
    for bad in [None, {}, [], "hi", {"text": 123}, {"text": ""},
                {"text": "   "}, {"text": "x" * 10_000, "speaker": "prospect"}]:
        r = trigger.should_fire(bad)
        assert r == {"fire": False, "question": "", "reason": "not_a_question"}


@pytest.mark.parametrize("raw", [
    "mocked response",
    '```json\n{"fire": true, "question": "Q?", "reason": "technical"}\n```',
    'Sure! {"fire": true, "question": "Q?", "reason": "technical"}',
    '{"fire": true, "question": "Q?", "reason": "smalltalk"}',
    '{"fire": true, "question": "", "reason": "technical"}',
    '{"fire": true, "question": "Q?", "reason": "technical", "extra": 1}',
    '{"fire": "yes", "question": "Q?", "reason": "technical"}',
    "",
])
def test_strict_parse_fails_closed(monkeypatch, raw):
    monkeypatch.setattr(trigger, "USE_MOCK", False)
    monkeypatch.setattr(model_client, "fast_complete", lambda *a, **k: raw)
    trigger.reset_call()
    r = trigger.should_fire({"text": "Do you support quantum sync?",
                             "speaker": "prospect", "ts": 1.0})
    assert r == {"fire": False, "question": "", "reason": "not_a_question"}


def test_strict_parse_accepts_exact_contract(monkeypatch):
    monkeypatch.setattr(trigger, "USE_MOCK", False)
    monkeypatch.setattr(model_client, "fast_complete",
                        lambda *a, **k: '{"fire": true, "question": "Do you support X?", "reason": "technical"}')
    trigger.reset_call()
    r = trigger.should_fire({"text": "Do you support X?", "speaker": "prospect", "ts": 1.0})
    assert r == {"fire": True, "question": "Do you support X?", "reason": "technical"}


def test_real_mode_pricing_denied_without_model_call(monkeypatch):
    monkeypatch.setattr(trigger, "USE_MOCK", False)
    calls = []
    monkeypatch.setattr(model_client, "fast_complete",
                        lambda *a, **k: calls.append(a) or "")
    trigger.reset_call()
    r = trigger.should_fire({"text": "How much does the enterprise tier cost?",
                             "speaker": "prospect", "ts": 1.0})
    assert r["fire"] is False and r["reason"] == "smalltalk"
    assert calls == []


def test_mem0_failure_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(trigger, "USE_MOCK", True)
    monkeypatch.setattr(trigger, "USE_MEM0", True)  # mem0 not installed here
    trigger.reset_call()
    q = {"text": "Are you SOC 2 certified?", "speaker": "prospect", "ts": 1.0}
    assert trigger.should_fire(q)["fire"] is True
    r = trigger.should_fire({**q, "text": "Are you SOC 2 compliant?"})
    assert r["reason"] == "repeat"
