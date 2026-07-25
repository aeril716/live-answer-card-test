"""Tests for retrieval.answer().

The offline contract (USE_MOCK=True) is asserted with no network and no vector
store. A second group exercises the real search path but SKIPS cleanly when the
persisted store has not been built, so `pytest` is always green offline.
"""

import importlib

import pytest

import retrieval


# --------------------------------------------------------------------------
# Mock-mode contract — must hold offline, no network, no store.
# --------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _force_mock(monkeypatch):
    monkeypatch.setattr(retrieval, "USE_MOCK", True)


REQUIRED_KEYS = {"keywords", "detail", "source", "confidence"}


def _assert_shape(card):
    assert set(card.keys()) == REQUIRED_KEYS
    assert isinstance(card["keywords"], list)
    assert isinstance(card["detail"], str)
    assert isinstance(card["source"], str)
    assert isinstance(card["confidence"], float)
    assert len(card["keywords"]) <= 3
    # A shown card (any keywords) must carry a source; contract forbids blanks.
    if card["keywords"]:
        assert card["source"], "a card with keywords must have a non-empty source"


def test_soc2_returns_card_above_threshold():
    card = retrieval.answer("Are you SOC 2 certified?")
    _assert_shape(card)
    assert card["confidence"] > 0.6
    assert len(card["keywords"]) == 3
    assert card["source"] == "security-overview.md §1.1"


def test_retention_returns_different_card():
    card = retrieval.answer("How long do you retain data?")
    _assert_shape(card)
    assert card["confidence"] > 0.6
    assert card["source"] == "security-overview.md §3"


def test_self_host_returns_third_card():
    card = retrieval.answer("Can we self-host Traces?")
    _assert_shape(card)
    assert card["confidence"] > 0.6
    assert card["source"] == "company-overview.md §4"


def test_three_mock_cards_are_distinct():
    a = retrieval.answer("Are you SOC 2 certified?")
    b = retrieval.answer("How long do you retain data?")
    c = retrieval.answer("Can we self-host Traces?")
    assert len({a["source"], b["source"], c["source"]}) == 3


def test_unknown_question_is_empty():
    card = retrieval.answer("What is the meaning of life?")
    assert card == retrieval.EMPTY


@pytest.mark.parametrize("bad", [None, "", "   ", 123, {}, []])
def test_bad_input_returns_empty_never_raises(bad):
    card = retrieval.answer(bad)
    assert card == retrieval.EMPTY


def test_never_more_than_three_keywords():
    for q in ("Are you SOC 2 certified?", "How long do you retain data?", "Can we self-host Traces?"):
        assert len(retrieval.answer(q)["keywords"]) <= 3


def test_never_a_card_with_empty_source():
    for q in ("Are you SOC 2 certified?", "How long do you retain data?", "Can we self-host Traces?"):
        card = retrieval.answer(q)
        if card["keywords"]:
            assert card["source"] != ""


def test_empty_constant_is_the_frozen_shape():
    assert retrieval.EMPTY == {"keywords": [], "detail": "", "source": "", "confidence": 0.0}


def test_mock_makes_no_network_call(monkeypatch):
    # If mock mode ever reached search(), this would raise.
    def _boom(*a, **k):
        raise AssertionError("search() must not be called in USE_MOCK mode")
    monkeypatch.setattr(retrieval, "search", _boom)
    assert retrieval.answer("Are you SOC 2 certified?")["source"] == "security-overview.md §1.1"


def test_answer_never_raises_on_internal_error(monkeypatch):
    monkeypatch.setattr(retrieval, "USE_MOCK", False)

    def _boom(*a, **k):
        raise RuntimeError("store exploded")
    monkeypatch.setattr(retrieval, "search", _boom)
    assert retrieval.answer("Are you SOC 2 certified?") == retrieval.EMPTY


def test_log_line_emitted(capsys):
    retrieval.answer("Are you SOC 2 certified?")
    out = capsys.readouterr().out
    assert "[retrieval] in=" in out and "out_conf=" in out


# --------------------------------------------------------------------------
# Confidence calibration is monotonic and low-biased (pure function, offline).
# --------------------------------------------------------------------------

def test_confidence_is_capped_and_low_biased():
    assert retrieval._confidence([{"source": "x", "score": 1.0}]) <= 0.95
    assert retrieval._confidence([]) == 0.0


def test_confidence_monotonic_in_score():
    lo = retrieval._confidence([{"source": "x", "score": 0.62}])
    hi = retrieval._confidence([{"source": "x", "score": 0.90}])
    assert hi > lo


def test_confidence_below_knee_stays_below_threshold():
    # An out-of-corpus-like weak score must not clear the 0.6 render gate.
    assert retrieval._confidence([{"source": "x", "score": 0.50}]) < 0.6


# --------------------------------------------------------------------------
# Real search path — skipped when the store is absent so offline stays green.
# --------------------------------------------------------------------------

def _store_ready():
    try:
        from ingest import search
        return bool(search("SOC 2", k=1))
    except Exception:
        return False


real_store = pytest.mark.skipif(not _store_ready(), reason="vector store not built")

ACCEPTANCE = [
    ("Are you SOC 2 certified?", "security-overview.md", "security-overview.md §1.1"),
    ("Do you train models on our data?", "security-overview.md", None),
    ("How long does Gateway keep request logs?", "security-overview.md", "security-overview.md §3"),
    ("Can we self-host Traces?", "company-overview.md", None),
    ("Do you support OpenTelemetry?", "integrations.md", None),
    ("What's the uptime commitment for Gateway?", "sla.md", None),
    ("How much latency does the proxy add on a cache hit?", "gateway-spec.md", None),
    ("Are you ISO 27001 certified?", "security-overview.md", None),
    ("How long do you retain trace data?", "security-overview.md", "security-overview.md §3"),
    ("How long is Evals data kept?", "security-overview.md", "security-overview.md §3"),
    ("How long do you retain data?", "security-overview.md", "security-overview.md §3"),
]


@real_store
@pytest.mark.parametrize("question,exp_doc,exp_section", ACCEPTANCE)
def test_acceptance_questions_real_path(monkeypatch, question, exp_doc, exp_section):
    monkeypatch.setattr(retrieval, "USE_MOCK", False)
    card = retrieval.answer(question)
    assert card["confidence"] >= 0.6, f"{question} -> {card['confidence']}"
    assert card["source"].startswith(exp_doc), f"{question} -> {card['source']}"
    assert card["keywords"], "confident card must have keywords"
    assert card["source"], "confident card must have a source"
    assert len(card["keywords"]) <= 3
    if exp_section is not None:
        assert card["source"] == exp_section


@real_store
def test_soc2_exact_section_real_path(monkeypatch):
    monkeypatch.setattr(retrieval, "USE_MOCK", False)
    assert retrieval.answer("Are you SOC 2 certified?")["source"] == "security-overview.md §1.1"


@real_store
@pytest.mark.parametrize("question", [
    "Do you have a Databricks connector?",
    "Who is your CEO?",
    "What's your carbon footprint?",
    "So how was your weekend?",
])
def test_out_of_corpus_stays_blank_real_path(monkeypatch, question):
    monkeypatch.setattr(retrieval, "USE_MOCK", False)
    assert retrieval.answer(question) == retrieval.EMPTY
