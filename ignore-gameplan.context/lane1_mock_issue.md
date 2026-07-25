# Lane 1 — mock issue

**Title:** `[Lane 1] retrieval.answer() — mock version`
**Label:** `pdd-change`

Copy everything below the line into the issue body.

---

## Goal

`retrieval.py` exposes `answer(question)` returning a keyword card. Mock only —
real search over the corpus comes in a later issue. This unblocks Lane 4, which
cannot build the screen without something to render.

## Contract — frozen

```python
def answer(question: str) -> dict:
    return {
        "keywords": ["SOC 2 — YES", "TYPE II", "NDA → REPORT"],
        "detail": "SOC 2 Type II, renewed March 2026 after an external audit.",
        "source": "security-overview.md §1.1",
        "confidence": 0.91,
    }

EMPTY = {"keywords": [], "detail": "", "source": "", "confidence": 0.0}
```

## Acceptance criteria

1. Given `USE_MOCK = True` at the top of the file, when `answer()` is called,
   then it returns canned data immediately and makes no network call.
2. Given a question containing "SOC 2", then a card with three keywords and
   confidence above 0.6 is returned.
3. Given a question about data retention, then a different canned card is
   returned.
4. Given a question about self-hosting, then a third canned card is returned.
5. Given any other question, then EMPTY is returned — so the empty screen can be
   demonstrated.
6. Given any internal error, then EMPTY is returned and nothing is raised.
7. Given the module runs, then it prints one line per call in the form
   `[retrieval] in=<question> out_conf=<confidence>`.

## Must not

- Must not raise under any circumstance.
- Must not import chromadb, requests, or any network library in this issue.
- Must not return more than three keywords.
- Must not return a card with an empty `source` field.

## Validation

- Run `python retrieval.py`. A `__main__` block calls the three known questions
  plus one unknown one and prints all four results.

## Done when

- `answer()` returns a valid card for the three known questions
- An unknown question returns EMPTY
- `python retrieval.py` runs clean with no network
