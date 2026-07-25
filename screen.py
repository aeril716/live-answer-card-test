"""Terminal preview renderer for the Live Answer Card support screen."""

import math

CONFIDENCE_THRESHOLD = 0.6
MAX_KEYWORDS = 3
REQUIRED_KEYS = ("keywords", "detail", "source", "confidence")
_CONTROL_CHARS = frozenset(chr(c) for c in range(0x20)) | {chr(0x7F)}


def _has_control_chars(text):
    return any(ch in _CONTROL_CHARS for ch in text)


def _clean_text(value):
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or _has_control_chars(value):
        return None
    return text


def _clean_keywords(value):
    if not isinstance(value, (list, tuple)) or not value:
        return None
    cleaned = []
    for item in value:
        text = _clean_text(item)
        if text is None:
            return None
        cleaned.append(text)
    return cleaned


def _clean_confidence(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return float(value)


def _confidence_token(card):
    if not isinstance(card, dict) or "confidence" not in card:
        return "None"
    return repr(card["confidence"])


def _normalize(card):
    """Returns (keywords, source, confidence), or None if the card can't be trusted."""
    if not isinstance(card, dict):
        return None
    if not all(key in card for key in REQUIRED_KEYS):
        return None

    keywords = _clean_keywords(card["keywords"])
    source = _clean_text(card["source"])
    confidence = _clean_confidence(card["confidence"])
    detail = card["detail"]

    if keywords is None or source is None or confidence is None or not isinstance(detail, str):
        return None

    return keywords[:MAX_KEYWORDS], source, confidence


def _box(lines):
    width = max(len(line) for line in lines)
    border = "+" + "-" * (width + 2) + "+"
    body = "\n".join("| " + line.ljust(width) + " |" for line in lines)
    return "\n".join([border, body, border])


def _render_card(keywords, source):
    print(_box([kw.upper() for kw in keywords] + [source]))


def _render_empty():
    print(_box(["-"]))


def render(card: dict) -> None:
    """Draws the card. Below 0.6 confidence, draws the empty state instead."""
    try:
        conf_token = _confidence_token(card)
    except Exception:
        conf_token = "None"

    try:
        normalized = _normalize(card)
    except Exception:
        normalized = None

    if normalized is not None:
        keywords, source, confidence = normalized
        if confidence >= CONFIDENCE_THRESHOLD:
            try:
                _render_card(keywords, source)
                print(f"[screen] in=conf={conf_token} out=rendered")
                return
            except Exception:
                pass  # fall through to the empty state

    try:
        _render_empty()
    except Exception:
        pass
    print(f"[screen] in=conf={conf_token} out=empty")


if __name__ == "__main__":
    full_card = {
        "keywords": ["SOC 2 — YES", "TYPE II", "NDA → REPORT"],
        "detail": "SOC 2 Type II, renewed March 2026 after an external audit.",
        "source": "security-overview.md §1.1",
        "confidence": 0.91,
    }
    low_confidence_card = {**full_card, "confidence": 0.4}
    five_keyword_card = {
        **full_card,
        "keywords": ["SOC 2 — YES", "TYPE II", "NDA → REPORT", "ISO 27001", "PEN TESTED"],
    }

    for label, card in (
        ("full card", full_card),
        ("confidence 0.4", low_confidence_card),
        ("empty dict", {}),
        ("five keywords", five_keyword_card),
    ):
        print(f"--- {label} ---")
        render(card)
        print()
