"""retrieval.answer() — the Lane 1 keyword-card producer.

    answer(question: str) -> dict
        {"keywords": list[str], "detail": str, "source": str, "confidence": float}

The card is the second-screen answer during a live sales call: two or three
large keywords the rep can glance at and say. The governing rules (see
context/project_preamble.prompt):

  * SILENCE beats a wrong card. Below the 0.6 confidence threshold we return the
    designed empty state — no keywords, no source.
  * NEVER raise. Any internal error returns EMPTY.
  * NEVER return a card with an empty source (an answer you can't trace is
    useless on a call).
  * At most three keywords, the first one carrying the answer.

USE_MOCK = True (the default) returns hand-authored cards with zero network, so
every test runs offline. USE_MOCK = False runs the real path: ingest.search()
over the persisted corpus store, then keyword generation.

Keyword generation is model-first with a passage-grounded floor: fast_complete()
is called for punchier labels, but any keyword not literally grounded in the
retrieved passage is dropped. When the model returns "" (any provider failure or
timeout) or nothing grounded survives, keywords are built from the top chunk's
HEADING instead — the section topic is a guaranteed, correct anchor. Rationale:
"a wrong keyword is much worse than a blank one" — an ungrounded model keyword is
exactly the failure this product cannot have.
"""

import os
import re

import model_client
from ingest import search

# Same env var ingest.search() already reads, so one flag flips both the
# card-level shortcut here and the store-level query together. Unset (local
# dev/tests) keeps the current mock default; explicitly "false" goes real.
USE_MOCK: bool = os.getenv("RETRIEVAL_USE_MOCK", "true").strip().lower() not in (
    "0", "false", "no",
)

EMPTY = {"keywords": [], "detail": "", "source": "", "confidence": 0.0}

CONFIDENCE_THRESHOLD = 0.6
MAX_KEYWORDS = 3

# Confidence calibration (see the PR "confidence" section). Raw hybrid search
# score for the canonical test questions clusters >= ~0.62; out-of-corpus / small
# talk queries sit <= ~0.53. We map that knee to the 0.6 render threshold and cap
# at 0.95 so the card is never shown as certain — "biased low" by construction.
_SCORE_KNEE = 0.57
_CONF_AT_KNEE = 0.60
_CONF_CAP = 0.95


# --- mock cards -----------------------------------------------------------
# Three canned cards keyed to the demo beats, each consistent with corpus/.
# Any other question returns EMPTY so the empty state stays reachable.

def _mock_answer(question: str) -> dict:
    q = question.lower()
    if "soc 2" in q or "soc2" in q or "soc ii" in q:
        return {
            "keywords": ["SOC 2 — YES", "TYPE II", "NDA → REPORT"],
            "detail": "SOC 2 Type II across all products, renewed March 2026 after an external audit.",
            "source": "security-overview.md §1.1",
            "confidence": 0.91,
        }
    if "retain" in q or "retention" in q or "keep" in q or ("how long" in q and "data" in q):
        return {
            "keywords": ["TRACES 90D", "GATEWAY 7D", "EVALS ∞"],
            "detail": "Retention differs by product: Traces 90 days, Gateway request logs 7 days, Evals indefinite.",
            "source": "security-overview.md §3",
            "confidence": 0.86,
        }
    if "self-host" in q or "self host" in q or "selfhost" in q or "on-prem" in q or "on prem" in q:
        return {
            "keywords": ["SELF-HOST — YES", "TRACES & GATEWAY", "EVALS CLOUD-ONLY"],
            "detail": "Traces and Gateway self-host in your VPC; Evals is cloud-only.",
            "source": "company-overview.md §4",
            "confidence": 0.84,
        }
    return dict(EMPTY)


# --- confidence -----------------------------------------------------------

def _confidence(hits: list) -> float:
    """Map hybrid retrieval score (+ margin) to a low-biased confidence."""
    if not hits:
        return 0.0
    top = float(hits[0]["score"])
    if top >= _SCORE_KNEE:
        conf = _CONF_AT_KNEE + (top - _SCORE_KNEE) * (
            (_CONF_CAP - _CONF_AT_KNEE) / (1.0 - _SCORE_KNEE)
        )
    else:
        conf = top / _SCORE_KNEE * _CONF_AT_KNEE

    # Ambiguity dampener: if the #2 hit is a DIFFERENT source and nearly ties the
    # top, we are not sure which passage answers — pull confidence down so the
    # screen is more likely to stay blank (the "response time" trap: support SLA
    # vs proxy latency live in different docs).
    if len(hits) > 1 and hits[1].get("source") != hits[0].get("source"):
        margin = top - float(hits[1]["score"])
        if margin < 0.04:
            conf *= 0.85

    return max(0.0, min(_CONF_CAP, conf))


# --- keyword / detail extraction -----------------------------------------

_ANSWER_WORDS = ("yes", "no", "type ii", "indefinite", "supported", "not")
_STOP = frozenset("""
a an the is are was were be to in on at of for and or how long do does you your
we our can could what when it its that this with from as per each their
""".split())


def _q_tokens(question):
    return {t for t in re.split(r"[^a-z0-9]+", question.lower())
            if len(t) >= 3 and t not in _STOP}


def _shorten(phrase: str, limit: int = 24) -> str:
    phrase = re.sub(r"\s+", " ", phrase).strip(" .,:;—-")
    if len(phrase) <= limit:
        return phrase
    cut = phrase[:limit]
    if " " in cut:                       # don't truncate mid-word
        cut = cut[:cut.rfind(" ")]
    return cut.strip(" .,:;—-")


def _heading_and_body(text: str):
    """Split a chunk into (heading_title, body).

    Chunk line 1 is ``<doc> — §<N> <Section Title>``; the section title is the
    passage's topic and the anchor for heading-based keywords.
    """
    lines = text.split("\n")
    heading_title = ""
    m = re.search(r"§\S+\s+(.*)$", lines[0]) if lines else None
    if m:
        heading_title = m.group(1).split("—")[0].strip()
    body = "\n".join(lines[1:]) if len(lines) > 1 else text
    return heading_title, body


def _candidate_phrases(text: str):
    """Ordered candidate keyphrases pulled from a retrieved chunk.

    The corpus bolds its key facts and renders table rows as ``k: v; k: v``;
    both are mined here so every keyword is literally present in the passage.
    """
    heading_title, body = _heading_and_body(text)

    cands = []
    # Row-rendered "key: value" cells -> the value is the fact.
    for cell in re.split(r"[;\n]", body):
        if ":" in cell:
            val = cell.split(":", 1)[1].strip()
            if val and val.lower() not in ("yes", "no"):
                cands.append(val)
    # Bold spans are author-marked key facts.
    cands += re.findall(r"\*\*(.+?)\*\*", body)
    # Durations / percentages / counts.
    cands += re.findall(r"\b\d[\w./%–-]*\s?(?:days?|hours?|ms|%|months?)\b", body, re.I)
    # Section title as a topical fallback.
    if heading_title:
        cands.append(heading_title)

    seen, out = set(), []
    for c in cands:
        s = _shorten(c)
        key = s.lower()
        if s and 2 <= len(s) and key not in seen and len(s.split()) <= 5:
            seen.add(key)
            out.append(s)
    return out


def _heading_keywords(question: str, text: str):
    """Keywords built from the top chunk's HEADING, enriched with grounded facts.

    This is the fallback the moment the model is unavailable — fast_complete()
    returns "" on any provider failure, and mock/ungrounded output is rejected.
    The section heading is the guaranteed topical anchor (so a confident card is
    never keyword-less); bolded facts, durations and table-cell values from the
    passage carry the actual answer and rank ahead of the heading by overlap
    with the question. Every keyword is literally present in the passage.
    """
    heading_title, _ = _heading_and_body(text)
    qtok = _q_tokens(question)
    cands = _candidate_phrases(text)

    def score(phrase):
        ptok = set(re.split(r"[^a-z0-9]+", phrase.lower()))
        overlap = len(qtok & ptok)
        has_num = 1 if re.search(r"\d", phrase) else 0
        is_heading = 1 if phrase.strip().lower() == heading_title.lower() else 0
        # answer-carrying facts first; the heading is the guaranteed floor, not
        # the lead, so it sorts last among ties.
        return (overlap, has_num, -is_heading, -len(phrase))

    ranked = sorted(cands, key=score, reverse=True)
    picked, seen = [], set()
    # Guarantee the heading topic is present so the card is always heading-rooted.
    heading_kw = _shorten(heading_title).upper() if heading_title else ""
    for p in ranked:
        up = p.upper()
        if up and up not in seen:
            seen.add(up)
            picked.append(up)
        if len(picked) >= MAX_KEYWORDS:
            break
    if heading_kw and heading_kw not in seen:
        if len(picked) < MAX_KEYWORDS:
            picked.append(heading_kw)
        else:
            picked[-1] = heading_kw
    return picked[:MAX_KEYWORDS]


def _parse_model_keywords(raw: str):
    """Parse fast_complete output into <=3 short keywords, or [] if unusable."""
    if not isinstance(raw, str) or not raw.strip():
        return []
    line = raw.strip().splitlines()[0]
    parts = re.split(r"\s*[|;,]\s*", line)
    out = []
    for p in parts:
        s = _shorten(p, 26)
        if s and len(s.split()) <= 4 and any(ch.isalnum() for ch in s):
            out.append(s.upper())
        if len(out) >= MAX_KEYWORDS:
            break
    return out


def _grounded(keyword: str, text: str) -> bool:
    """A model keyword is trusted only if its content words appear in the passage."""
    body = text.lower()
    words = [w for w in re.split(r"[^a-z0-9]+", keyword.lower())
             if len(w) >= 3 and w not in _ANSWER_WORDS]
    if not words:
        return True  # pure answer-word like "YES"/"NO" rides on its neighbours
    return any(w in body for w in words)


def _keywords_and_detail(question: str, top: dict):
    text = top.get("text", "")
    _, body = _heading_and_body(text)
    # Detail: first grounded sentence of the body (drop the heading context line).
    body = re.sub(r"\s+", " ", body.replace("*", "")).strip()
    detail = ""
    for sent in re.split(r"(?<=[.!?])\s+", body):
        if sent:
            detail = sent.strip()
            break
    detail = detail[:200]

    # Model first: fast_complete() phrases punchier labels when a real model is
    # configured. It returns "" on any failure/timeout (and a placeholder in mock
    # mode); either way, ungrounded output is rejected below.
    keywords = []
    try:
        prompt = (
            "You label a sales-call answer screen. From the passage, give 2-3 "
            "SHORT keyword labels (<=4 words each), pipe-separated, uppercase, "
            "the FIRST label stating the answer. No sentences.\n"
            f"Question: {question}\nPassage: {text}\nLabels:"
        )
        raw = model_client.fast_complete(prompt, max_tokens=40)
        keywords = [k for k in _parse_model_keywords(raw) if _grounded(k, text)]
    except Exception as exc:
        print(f"[retrieval] keyword-model error: {exc}")

    # No usable model keywords (empty completion, mock placeholder, or all
    # ungrounded) -> build them from the top chunk's heading instead.
    if not keywords:
        keywords = _heading_keywords(question, text)

    return keywords[:MAX_KEYWORDS], detail


# --- public interface -----------------------------------------------------

def answer(question: str) -> dict:
    confidence = 0.0
    try:
        if not isinstance(question, str) or not question.strip():
            print(f"[retrieval] in={question!r} out_conf=0.0")
            return dict(EMPTY)

        if USE_MOCK:
            card = _mock_answer(question)
            print(f"[retrieval] in={question} out_conf={card['confidence']}")
            return card

        hits = search(question, k=3)
        confidence = _confidence(hits)

        # Below threshold -> designed empty state. We skip keyword generation
        # entirely: it saves the latency and removes any chance of surfacing a
        # low-confidence (i.e. possibly wrong) card.
        if not hits or confidence < CONFIDENCE_THRESHOLD:
            print(f"[retrieval] in={question} out_conf={round(confidence, 3)}")
            return dict(EMPTY)

        top = hits[0]
        source = top.get("source", "")
        if not source:
            print(f"[retrieval] in={question} out_conf=0.0")
            return dict(EMPTY)

        keywords, detail = _keywords_and_detail(question, top)
        if not keywords:
            # Confident retrieval but no usable keyword — better blank than bare.
            print(f"[retrieval] in={question} out_conf=0.0")
            return dict(EMPTY)

        card = {
            "keywords": keywords[:MAX_KEYWORDS],
            "detail": detail,
            "source": source,
            "confidence": round(confidence, 3),
        }
        print(f"[retrieval] in={question} out_conf={card['confidence']}")
        return card

    except Exception as exc:
        print(f"[retrieval] error: {exc}")
        print(f"[retrieval] in={question!r} out_conf=0.0")
        return dict(EMPTY)


if __name__ == "__main__":
    for q in (
        "Are you SOC 2 certified?",
        "How long do you retain data?",
        "Can we self-host Traces?",
        "What is the meaning of life?",
    ):
        print(f"--- {q}")
        print(answer(q))
