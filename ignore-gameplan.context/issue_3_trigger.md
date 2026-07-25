# Issue #3 — Lane 3 · Trigger

**Owner:** Lane 3
**Label:** `pdd-change`
**Title:** `[Lane 3] trigger.should_fire() + model_client — the decision layer`
**Post after** issue #0 has finished. **Post this one first of the four** —
Lane 1 is blocked on `model_client.py`.

Copy everything below the line into the issue body.

---

## Goal

`trigger.should_fire(utterance)` decides whether the screen shows anything at
all, correctly classifying technical questions, small talk, repeats, and
non-questions. And `model_client.fast_complete()` gives the whole project one
provider-agnostic way to call a fast model.

## Context

This is the module the judges are actually evaluating. The claim we are making
on stage is "we designed a system rather than calling an LLM," and this module
is the entire evidence for that claim. Everything else is plumbing around it.

**Build `model_client.py` first** — Lane 1 cannot start real work without it.
Keep it under about 60 lines. It exists so that swapping or adding model
providers at the event is a `.env` edit rather than a code change, which matters
because sponsor rate limits and credits sometimes arrive late or not at all.

It should also support an optional secondary provider. If `FALLBACK_MODEL_*` is
set in `.env`, retry once against it when the primary times out or errors, and
print which provider actually served the call. If it isn't set, behave exactly
as before. Two providers configured means one provider going down or rate
limiting us does not stop the demo.

Then the classifier. Four decisions, in this order:

1. **Is this a question at all?** Statements and back-channel ("mm-hmm",
   "right", "gotcha") never fire.
2. **Is it technical or spec-related?** Pricing, scheduling, and small talk
   never fire, even when phrased as questions.
3. **Have we already answered this on this call?** Re-firing the same card is
   worse than never firing — it turns the screen into noise, and the rep stops
   trusting it.
4. **Is it phrased well enough for retrieval?** If not, rewrite it into a clean
   question string in the `question` field.

Do the cheap checks before the expensive one. Decisions 1 and 3 should mostly
resolve without a model call at all, which saves latency on every line of small
talk — and most of a sales call is small talk.

## Acceptance criteria

**model_client**

1. Given `.env` sets provider, model, base URL and key, when
   `fast_complete("hi")` is called, then it returns the model's text.
2. Given the request times out or errors, when `fast_complete()` is called, then
   it returns `""` and does not raise.
3. Given `USE_MOCK = True`, then it returns a canned string with no network
   access.
4. Given the primary provider errors and a fallback is configured, when
   `fast_complete()` is called, then the fallback serves it and the provider
   used is printed.
5. Given the primary provider errors and no fallback is configured, then it
   returns `""` without retrying.

**trigger**

6. Given the utterance "Are you SOC 2 certified?", when `should_fire()` is
   called, then `fire` is True and `reason` is `"technical"`.
7. Given the utterance "How was your weekend?", when `should_fire()` is called,
   then `fire` is False and `reason` is `"smalltalk"`.
8. Given the utterance "How much does the enterprise tier cost?", when
   `should_fire()` is called, then `fire` is False — pricing is not technical.
9. Given a question already answered earlier in the same call, when it is asked
   again in different words, then `fire` is False and `reason` is `"repeat"`.
10. Given "mm-hmm", when `should_fire()` is called, then `fire` is False and
   `reason` is `"not_a_question"`, with no model call made.
11. Given the model returns malformed JSON, when `should_fire()` is called, then
   it returns EMPTY and does not raise.
12. Given a 20-sentence labelled test set, when it is run, then at least 18
    sentences classify correctly and **no small-talk sentence fires**.

## Must not

- Must not raise under any circumstance — catch and return EMPTY.
- Must not fire on pricing, scheduling, or small talk.
- Must not fire twice for the same question within one call.
- Must not make a model call for back-channel or obvious non-questions.
- Must not accept a model response wrapped in markdown fences or preamble —
  parse strictly, fail to EMPTY.

## Optimisation target — state this in the PR too

**Precision over recall.** A missed question is a small loss. A card that fires
during small talk destroys the demo and the argument behind it. Bias every
threshold accordingly, and say in a code comment exactly where that bias lives,
so it can be moved during rehearsal without hunting.

## Repeat detection

Start with the simple version: a list of answered questions for this call plus a
similarity check. Explain the tradeoff of the approach chosen.

Then, behind a `USE_MEM0` flag, show what it takes to back this with **mem0**
instead. mem0 is a hackathon sponsor and this is the one place in our system
where a real memory layer is genuinely the right tool rather than decoration.
The simple version stays as the fallback and remains the default.

## Validation

- Test: `pytest tests/test_trigger.py -q` — the 20-sentence labelled set,
  running entirely against mocks with no network access.
- The test set must include the hard cases: a technical question buried in small
  talk, the same question asked twice in different words, and a question
  addressed to the rep's colleague rather than to us.
- A debug mode that prints, per sentence, which of the four decisions stopped it
  and why. Needed for tuning, and for explaining the system on stage.

## Done when

- `model_client.py` works and Lane 1 is unblocked
- The 20-sentence test set passes at 18/20 or better
- Zero small-talk sentences fire — this is a hard gate, not a target
- The debug output makes every decision explainable in one line
