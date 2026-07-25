# Lane 3 — mock issue

**Title:** `[Lane 3] trigger.should_fire() — mock version`
**Label:** `pdd-change`

Copy everything below the line into the issue body.

---

## Goal

`trigger.py` exposes `should_fire(utterance)` deciding whether the screen shows
anything at all. Mock only — the real classifier comes in a later issue.

This is the core of the product. Answering is the easy half; deciding when to
stay silent is what we are actually building.

## Contract — frozen

```python
def should_fire(utterance: dict) -> dict:
    return {"fire": True,
            "question": "Are you SOC 2 certified?",
            "reason": "technical"}
    # reason: "technical" | "smalltalk" | "repeat" | "not_a_question"

EMPTY = {"fire": False, "question": "", "reason": "not_a_question"}
```

## Acceptance criteria

1. Given `USE_MOCK = True` at the top of the file, when `should_fire()` is
   called, then it decides from a hardcoded lookup and makes no network call.
2. Given a SOC 2 question, then `fire` is True and `reason` is `"technical"`.
3. Given a Type I or Type II follow-up, then `fire` is True and `reason` is
   `"technical"`.
4. Given a question about the weekend, then `fire` is False and `reason` is
   `"smalltalk"`.
5. Given a pricing question, then `fire` is False and `reason` is `"smalltalk"`.
   Pricing is excluded by design — it is the rep's conversation to have.
6. Given "mm-hmm", then `fire` is False and `reason` is `"not_a_question"`.
7. Given an utterance not in the lookup, then EMPTY is returned. Silence is the
   safe default.
8. Given a question that already fired earlier in the same call, when it is
   passed again, then `fire` is False and `reason` is `"repeat"`.
9. Given any internal error, then EMPTY is returned and nothing is raised.
10. The module prints one line per call in the form
    `[trigger] in=<text> fire=<bool> reason=<reason>`.

## Must not

- Must not raise under any circumstance.
- Must not fire on pricing, scheduling, or small talk.
- Must not fire twice for the same question in one call.
- Must not import requests or any model library in this issue.

## Validation

- Run `python trigger.py`. A `__main__` block runs all five cases plus a repeat
  of the SOC 2 question and prints each decision.

## Done when

- All five cases classify correctly
- The repeated SOC 2 question returns `reason: "repeat"`
- No small-talk or pricing line fires — this is a hard gate
