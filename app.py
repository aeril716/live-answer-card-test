"""Live Answer Card — the single entry point. Run: streamlit run app.py

Wires audio.get_utterance() -> trigger.should_fire() -> retrieval.answer()
-> the card display. Two modes from the sidebar: Live (polling loop) and
Typed (microphone-failure fallback). Missing modules are replaced by stubs
returning their frozen EMPTY values so the app always boots. (issue #13)
"""
import importlib
import time
from types import SimpleNamespace

USE_MOCK = True  # the app itself touches no network; modules own their flags

CONFIDENCE_THRESHOLD = 0.6

EMPTY_UTTERANCE = {"text": "", "speaker": "unknown", "ts": 0.0}
EMPTY_DECISION = {"fire": False, "question": "", "reason": "not_a_question"}
EMPTY_CARD = {"keywords": [], "detail": "", "source": "", "confidence": 0.0}


def _stub(name):
    return SimpleNamespace(
        get_utterance=lambda: dict(EMPTY_UTTERANCE),
        should_fire=lambda u: dict(EMPTY_DECISION),
        reset_call=lambda: None,
        answer=lambda q: dict(EMPTY_CARD),
        render=lambda card: print(f"[app] ({name} stub) card={card}"),
        _is_stub=True,
    )


def load_modules():
    """Import the four lane modules; stub whatever is missing."""
    mods, missing = {}, []
    for name in ("audio", "trigger", "retrieval", "screen"):
        try:
            mods[name] = importlib.import_module(name)
        except Exception as e:
            print(f"[app] {name} unavailable ({e}); using stub")
            mods[name] = _stub(name)
            missing.append(name)
    return mods, missing


def process_utterance(mods, utterance):
    """One pass of the loop. Returns a card dict, or None when silent."""
    try:
        if not utterance or not utterance.get("text"):
            return None
        decision = mods["trigger"].should_fire(utterance)
        if not decision.get("fire"):
            return None
        return mods["retrieval"].answer(decision.get("question", ""))
    except Exception as e:
        print(f"[app] loop error: {e}")
        return None


_CARD_CSS = """
<style>
header[data-testid="stHeader"], #MainMenu, footer {display:none;}
.lac-card{
  background:#111E42; border:1px solid #243560; border-radius:16px;
  padding:34px 38px; margin-top:8px;
}
.lac-card .kw{
  font-size:clamp(30px,5.2vw,54px); font-weight:800; line-height:1.18;
  letter-spacing:.01em; color:#F2F5FB; text-transform:uppercase;
}
.lac-card .kw:first-child{color:#FFC94D;}
.lac-card .det{margin-top:16px; color:#B7BFCF; font-size:15px; line-height:1.5;}
.lac-card .src{
  margin-top:8px; color:#8B96B0; font-size:13px;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
}
.lac-card.lac-empty{text-align:center; color:#5A6685; padding:44px 38px;}
.lac-card.lac-empty .dash{font-size:46px; line-height:1;}
.lac-card.lac-empty .lst{
  margin-top:10px; font-size:12px; letter-spacing:.18em; text-transform:uppercase;
}
</style>
"""


def _card_markdown(card):
    # One single markdown element: st.empty() replaces it atomically, which
    # avoids ghost fragments from partially-replaced multi-element cards.
    # Look follows ignore-gameplan.context/live_answer_card_prototype.html.
    import html as _html
    card = card or {}
    keywords = [str(k) for k in card.get("keywords", [])][:3]
    if card.get("confidence", 0.0) >= CONFIDENCE_THRESHOLD and keywords:
        kws = "".join(f'<div class="kw">{_html.escape(k)}</div>' for k in keywords)
        detail = _html.escape(card.get("detail", ""))
        source = _html.escape(card.get("source", ""))
        return (f'<div class="lac-card">{kws}'
                f'<div class="det">{detail}</div>'
                f'<div class="src">{source}</div></div>')
    return ('<div class="lac-card lac-empty"><div class="dash">—</div>'
            '<div class="lst">listening</div></div>')


def _run_app():
    import streamlit as st

    st.set_page_config(page_title="Live Answer Card", page_icon="📇")
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    mods, missing = load_modules()

    st.sidebar.title("Live Answer Card")
    if missing:
        st.sidebar.warning("Stubbed (not on main yet): " + ", ".join(missing))
    mode = st.sidebar.radio("Mode", ["Typed", "Live"], index=0)
    st.session_state.setdefault("running", False)

    if mode == "Typed":
        st.session_state.running = False  # toggle stops the loop
        q = st.text_input("Question")
        if q:
            card = mods["retrieval"].answer(q)
            mods["screen"].render(card)
            st.markdown(_card_markdown(card), unsafe_allow_html=True)

    else:  # Live
        col_a, col_b = st.sidebar.columns(2)
        if col_a.button("Start"):
            if getattr(mods["audio"], "USE_MOCK", False):
                # replay the rehearsed mock call from the top on every Start
                mods["audio"] = importlib.reload(mods["audio"])
            mods["trigger"].reset_call()
            st.session_state.running = True
        if col_b.button("Stop"):
            st.session_state.running = False

        placeholder = st.empty()
        placeholder.markdown(_card_markdown(None), unsafe_allow_html=True)
        mock_audio = getattr(mods["audio"], "USE_MOCK", False)
        empties = 0
        while st.session_state.running:
            u = mods["audio"].get_utterance()
            if not u.get("text"):
                empties += 1
                if empties > 100:  # mock sequence exhausted; stop cleanly
                    st.session_state.running = False
                    break
                time.sleep(0.1)
                continue
            empties = 0
            card = process_utterance(mods, u)
            if card is not None:
                mods["screen"].render(card)
                placeholder.markdown(_card_markdown(card), unsafe_allow_html=True)
            if mock_audio:
                time.sleep(2.0)  # pace the replayed call so cards are watchable


def _streamlit_active():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


if _streamlit_active():
    _run_app()

if __name__ == "__main__" and not _streamlit_active():
    # Offline validation without a UI: play the mock audio sequence through
    # the full loop and print every decision and card.
    mods, missing = load_modules()
    print(f"[app] modules loaded, stubbed: {missing or 'none'}")
    mods["trigger"].reset_call()
    for _ in range(6):
        u = mods["audio"].get_utterance()
        if not u.get("text"):
            print("[app] (audio exhausted)")
            continue
        card = process_utterance(mods, u)
        if card is not None:
            mods["screen"].render(card)
        else:
            print("[app] silent")
