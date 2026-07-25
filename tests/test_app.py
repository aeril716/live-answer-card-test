"""Smoke tests for app.py helpers — offline, no Streamlit runtime needed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app


def test_load_modules_stubs_missing_retrieval():
    mods, missing = app.load_modules()
    assert "retrieval" in missing  # not on main yet
    card = mods["retrieval"].answer("Are you SOC 2 certified?")
    assert card == app.EMPTY_CARD


def test_loaded_real_modules_are_not_stubs():
    mods, missing = app.load_modules()
    for name in ("audio", "trigger", "screen"):
        assert name not in missing
        assert not getattr(mods[name], "_is_stub", False)


def test_process_utterance_full_mock_loop_never_raises():
    mods, _ = app.load_modules()
    mods["trigger"].reset_call()
    saw_card = False
    for _ in range(6):
        u = mods["audio"].get_utterance()
        card = app.process_utterance(mods, u)
        if card is not None:
            saw_card = True
            assert set(card.keys()) == set(app.EMPTY_CARD.keys())
    assert saw_card  # the SOC 2 mock utterance fires through the stub


def test_process_utterance_handles_garbage():
    mods, _ = app.load_modules()
    for bad in (None, {}, {"text": ""}, {"text": None}):
        assert app.process_utterance(mods, bad) is None


def test_importing_app_does_not_require_streamlit_runtime():
    assert app._streamlit_active() is False
