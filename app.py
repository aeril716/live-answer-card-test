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
.block-container{padding-top:1.4rem; max-width:1000px;}
.lac{font-family:inherit;}
.lac .bar{display:flex; align-items:center; gap:14px; padding-bottom:14px;
  border-bottom:1px solid #243560; margin-bottom:22px;}
.lac .prod{font-size:15px; font-weight:700; letter-spacing:.14em; color:#4DA3FF;}
.lac .prod span{color:#8B96B0; font-weight:400; letter-spacing:.02em; margin-left:10px;}
.lac .liv{margin-left:auto; display:flex; align-items:center; gap:8px;
  font-size:12px; font-weight:700; letter-spacing:.18em; color:#4DA3FF;}
.lac .dot{width:9px; height:9px; border-radius:50%; background:#4DA3FF;
  animation:lacpulse 1.6s infinite;}
@keyframes lacpulse{0%,100%{opacity:1}50%{opacity:.25}}
@media (prefers-reduced-motion: reduce){.lac .dot{animation:none}}
.lac .row{display:flex; gap:16px; align-items:flex-start;}
.lac .tag{flex:0 0 auto; width:44px; height:44px; border-radius:10px;
  display:flex; align-items:center; justify-content:center;
  font-size:22px; font-weight:800;}
.lac .tag.q{background:#243560; color:#B7BFCF;}
.lac .tag.a{background:#FFFFFF; color:#0A1430;}
.lac .qtext{font-size:clamp(20px,3.2vw,30px); font-weight:500; line-height:1.25;
  color:#B7BFCF; padding-top:5px;}
.lac .who{display:block; font-size:12px; font-weight:700; letter-spacing:.18em;
  color:#5A6685; margin-bottom:6px;}
.lac .arow{margin-top:22px;}
.lac .chips{display:flex; flex-wrap:wrap; gap:14px;}
.lac .chip{border:2.5px solid #FFFFFF; background:#16265b; color:#FFFFFF;
  border-radius:14px; padding:16px 24px;
  font-size:clamp(26px,4.6vw,44px); font-weight:800; letter-spacing:.01em;
  box-shadow:0 4px 18px rgba(0,0,0,.35);}
.lac .drawer{margin-top:18px; border-left:4px solid #FFFFFF; background:#111E42;
  border-radius:0 12px 12px 0; padding:18px 22px;}
.lac .drawer p{font-size:clamp(15px,2vw,19px); line-height:1.55; color:#F2F5FB; margin:0;}
.lac .src{margin-top:12px; font-size:13px; color:#8B96B0;}
.lac .src b{color:#4DA3FF; font-weight:700;}
.lac .conf{margin-top:16px; font-size:13px; color:#8B96B0;}
.lac .conf b{color:#FFC94D; font-weight:800;}
.lac .nothing{text-align:center; color:#5A6685; padding:48px 0 30px;}
.lac .nothing .big{font-size:clamp(22px,3.4vw,34px); font-weight:700; letter-spacing:.04em;}
.lac .nothing .why{margin-top:10px; font-size:14px; letter-spacing:.12em; font-weight:600;}
</style>
"""


def _card_markdown(card, question=""):
    # One single markdown element: st.empty() replaces it atomically, which
    # avoids ghost fragments. Faithful to
    # ignore-gameplan.context/live_answer_card_prototype.html: header bar with
    # pulsing LISTENING dot, Q row, white-bordered keyword chips, detail
    # drawer, and the deliberate "— nothing —" empty state.
    import html as _html
    card = card or {}
    keywords = [str(k) for k in card.get("keywords", [])][:3]
    fired = card.get("confidence", 0.0) >= CONFIDENCE_THRESHOLD and keywords

    head = ('<div class="bar"><span class="prod">VANTIC'
            '<span>sales support · live</span></span>'
            '<span class="liv"><span class="dot"></span>LISTENING</span></div>')
    qrow = ""
    if question:
        qrow = ('<div class="row"><div class="tag q">Q</div>'
                f'<div class="qtext"><span class="who">PROSPECT</span>'
                f'{_html.escape(question)}</div></div>')

    if fired:
        chips = "".join(f'<div class="chip">{_html.escape(k)}</div>' for k in keywords)
        detail = _html.escape(card.get("detail", ""))
        source = _html.escape(card.get("source", ""))
        conf = f"{card.get('confidence', 0.0):.2f}"
        body = (f'<div class="row arow"><div class="tag a">A</div><div>'
                f'<div class="chips">{chips}</div>'
                f'<div class="drawer"><p>{detail}</p>'
                f'<div class="src">Source: <b>{source}</b></div></div>'
                f'<div class="conf">CONFIDENCE <b>{conf}</b></div>'
                f'</div></div>')
    else:
        why = ("NOT A TECHNICAL QUESTION · SCREEN STAYS QUIET" if question
               else "LISTENING FOR A TECHNICAL QUESTION")
        body = (f'<div class="nothing"><div class="big">— nothing —</div>'
                f'<div class="why">{why}</div></div>')

    return f'<div class="lac">{head}{qrow}{body}</div>'


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
            st.markdown(_card_markdown(card, q), unsafe_allow_html=True)

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
            # redraw on every utterance: silence with the question visible IS
            # the product argument, so show it rather than freezing the card
            placeholder.markdown(_card_markdown(card, u.get("text", "")),
                                 unsafe_allow_html=True)
            if mock_audio:
                time.sleep(2.5)  # pace the replayed call so cards are watchable


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
