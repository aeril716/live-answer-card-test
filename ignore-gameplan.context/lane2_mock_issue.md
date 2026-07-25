# Lane 2 — mock issue

**Title:** `[Lane 2] audio.get_utterance() — mock version`
**Label:** `pdd-change`

Copy everything below the line into the issue body.

---

## Goal

`audio.py` exposes `get_utterance()` returning one utterance at a time. Mock
only — real ElevenLabs streaming comes in a later issue. This lets the whole
team run the loop without a microphone.

## Contract — frozen

```python
def get_utterance() -> dict:
    return {"text": "Are you guys SOC 2 certified?",
            "speaker": "prospect",
            "ts": 252.4}

EMPTY = {"text": "", "speaker": "unknown", "ts": 0.0}
```

## Acceptance criteria

1. Given `USE_MOCK = True` at the top of the file, when `get_utterance()` is
   called, then it replays a hardcoded list and makes no network call.
2. The hardcoded list contains, in this order: a technical question about SOC 2,
   a follow-up asking Type I or Type II, a small-talk line about the weekend,
   and a pricing question. This is the demo sequence.
3. Given repeated calls, then each utterance is returned exactly once, in order.
4. Given the list is exhausted, then EMPTY is returned on every later call.
5. Given the function is called, then it returns immediately and never blocks.
6. Given any internal error, then EMPTY is returned and nothing is raised.
7. `ts` increases across the list.
8. The module prints one line per call in the form `[audio] out=<text>`.

## Must not

- Must not raise under any circumstance.
- Must not block the calling thread.
- Must not return the same utterance twice.
- Must not import websockets, requests, or any audio library in this issue.

## Validation

- Run `python audio.py`. A `__main__` block calls `get_utterance()` six times
  and prints each result, so exhaustion is visible.

## Done when

- Four utterances come out in order, then EMPTY forever
- `python audio.py` runs clean with no microphone and no network
