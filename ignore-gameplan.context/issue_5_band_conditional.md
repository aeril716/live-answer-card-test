# Issue #5 — Band audit stream (CONDITIONAL)

**Owner:** Lane 3
**Label:** `pdd-change`
**Title:** `[Lane 3] Band audit room — decision stream for the call`

## Do not post this issue before 14:00

This exists for the Band sponsor prize — **$500 cash**, not the $2,000 we
assumed before seeing the prize board. The three main prizes ($2,300 / $1,100 /
$500) all require Render, so Render comes first and this is a bonus on top.

**Post it only if all of these are true at 14:00:**

- [ ] The main demo runs end to end with real retrieval and real trigger
- [ ] Lane 3's 20-sentence test set passes and zero small talk fires
- [ ] Nobody else is blocked on Lane 3
- [ ] The Band challenge rules (checked on-site) don't require something
      structurally different from what's below
- [ ] Render deployment is already done — it gates the main prizes and this
      does not

**Hard stop at 16:00.** If it isn't merged and working by feature freeze, revert
it and move on. A half-integrated sponsor tool at 17:00 costs far more in demo
quality than $500 is worth.

---

Copy everything below the line into the issue body.

---

## Goal

Every fire/no-fire decision made during a call is published to a Band room as an
audit record, without adding any latency to the answer path.

## Context

The trigger module already produces this data. Issue #3 requires per-utterance
reasoning output so decisions can be tuned and explained. Right now that goes to
`print()`. This change sends the same records to a shared Band room as well.

The result is a live audit trail of what the assistant surfaced during a sales
call and why:

```
FIRED      "Are you SOC 2 certified?"     technical   conf 0.91   security-overview.md §1.1
SILENT     "How was your weekend?"        smalltalk   —
SILENT     "How much is the Team plan?"   smalltalk   — (pricing excluded by design)
SILENT     "Are you SOC 2 compliant?"     repeat      — answered at 00:04:12
```

This is on our roadmap already — the PRD lists a post-call summary of every
question asked and how it was answered under Future Enhancements. This brings
that forward.

Why it matters beyond the prize: in regulated sales, what a rep claimed and what
backed the claim is a real audit question. A compliance reviewer opening the room
after the call is a genuine use, not a demo prop.

## The constraint that governs this entire change

**The answer path must not get slower.** Our whole product argument is a
three-second budget. Adding a network hop to the hot path would undermine the
thing we are on stage to claim.

Therefore:

- Publishing is **fire-and-forget**. Records go onto an in-memory queue; a
  background thread drains it.
- The queue push must be non-blocking and must complete in well under 1 ms.
- If the queue is full, **drop the record**. Never block, never grow unbounded.
- If Band is unreachable, unauthenticated, slow, or throwing, the call loop must
  behave exactly as if this feature did not exist.

## Acceptance criteria

1. Given `USE_BAND = False` (the default), when the system runs, then no Band
   code executes and no Band dependency is imported at call time.
2. Given `USE_BAND = True` and a firing decision, when `should_fire()` returns,
   then an audit record is enqueued and the function returns without waiting for
   any network call.
3. Given `USE_BAND = True` and a non-firing decision, then a record is enqueued
   with the reason (`smalltalk`, `repeat`, `not_a_question`).
4. Given the Band endpoint is unreachable, when 20 utterances are processed, then
   all 20 still produce correct decisions and the loop never blocks or raises.
5. Given the publish queue is full, when a new record arrives, then it is dropped
   and a single warning is printed — the queue never grows without bound.
6. Given a completed call, when the Band room is opened, then it contains one
   record per utterance in order, each showing the utterance, the decision, the
   reason, and for fired decisions the confidence and source.
7. Given `USE_BAND = True`, when end-to-end latency is measured over 20
   utterances, then the median is within 5 ms of the same run with
   `USE_BAND = False`.

Criterion 7 is the one that matters. If it fails, the feature is wrong regardless
of whether the room looks good.

## Must not

- Must not add any blocking call to `should_fire()`.
- Must not raise, ever — Band failures are logged and swallowed.
- Must not change the `should_fire()` contract. Its return value is unchanged.
- Must not put customer question text into the room if a `REDACT_QUESTIONS` flag
  is set — publish the decision and reason only.
- Must not require Band to be running for any test to pass.
- Must not become a dependency of the demo. If Band is down at 17:00 we flip the
  flag off and the demo is unaffected.

## Validation

- Test: `pytest tests/test_band.py -q` — runs with no network, using a fake
  publisher, and asserts criteria 1 through 5
- Manual: run the three demo questions plus two small-talk lines with
  `USE_BAND = True` and confirm five records appear in the room
- Manual: kill the network and confirm the demo is visually identical

## Done when

- The flag defaults to off and the demo is unaffected either way
- Latency delta is measured, not assumed
- The room shows both fired and silent decisions — the silent ones are the
  interesting half and the reason this is worth showing at all
