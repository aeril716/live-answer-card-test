# Lane 4 — mock issue

**Title:** `[Lane 4] screen.render() — mock version`
**Label:** `pdd-change`

Copy everything below the line into the issue body.

---

## Goal

`screen.py` exposes `render(card)` drawing the support screen. Terminal output
only in this issue — Streamlit comes later. This lets the full loop be tested
end to end before any UI exists.

## Contract — frozen

```python
def render(card: dict) -> None:
    """Draws the card. Below 0.6 confidence, draws the empty state instead."""
```

It receives:

```python
{
    "keywords": ["SOC 2 — YES", "TYPE II", "NDA → REPORT"],
    "detail": "SOC 2 Type II, renewed March 2026 after an external audit.",
    "source": "security-overview.md §1.1",
    "confidence": 0.91,
}
```

## Acceptance criteria

1. Given a card with confidence at or above 0.6, then the keywords print in a
   bordered box, uppercase, one per line, with the source underneath.
2. Given a card with confidence below 0.6, then the empty state draws instead.
3. Given an empty dict or a card missing keys, then the empty state draws and
   nothing is raised.
4. Given a card with five keywords, then only three render.
5. The empty state is a bordered box containing a dash — visibly deliberate,
   never a blank line or an error message. On stage we show it on purpose, to
   prove a decision layer exists.
6. Given `render()` is called, then it prints one line in the form
   `[screen] in=conf=<confidence> out=<rendered|empty>`.

## Must not

- Must not raise under any circumstance.
- Must not render more than three keywords.
- Must not import streamlit in this issue.
- Must not make the empty state look like an error, a crash, or a blank screen.

## Validation

- Run `python screen.py`. A `__main__` block renders four cases: a full card, a
  card at confidence 0.4, an empty dict, and a card with five keywords.

## Done when

- A full card renders with three keywords and a source
- Confidence 0.4 renders the empty state
- An empty dict renders the empty state without raising
