<!-- pdd-story-contract derived-from-story="../story__screen_stays_blank_when_unsure.md" story-hash="auto" issue-ref="8" -->

# Contract: screen_stays_blank_when_unsure

## Covers

- prompts/retrieval_python.prompt#R4: show a card only at confidence >= 0.6, else EMPTY
- prompts/retrieval_python.prompt#R8: never raise; errors return EMPTY

This is a negative story: it verifies the empty state is reached, not avoided.

## Context / Fixtures

The corpus store is built from `corpus/`. `answer()` runs in real mode. None of
the questions below are answerable from the six docs, and one is small talk.

## Acceptance Criteria

1. Given the built store,
   when `answer()` is called with "Do you have a Databricks connector?",
   "Who is your CEO?", or "What's your carbon footprint?",
   then it returns EMPTY.

2. Given the built store,
   when `answer("So how was your weekend?")` is called,
   then it returns EMPTY.

3. Given any internal error during `answer()`,
   then it returns EMPTY and does not raise.

## Oracle

- The returned value equals `EMPTY`
  (`{"keywords": [], "detail": "", "source": "", "confidence": 0.0}`).
- No exception propagates.

## Non-Oracle

- Which passage happened to rank first internally does not matter.
- The internal confidence computed before the threshold does not matter.

## Negative Cases

- Must not return a card with confidence >= 0.6 for any question above.
- Must not raise for malformed or non-string input.

## Candidate Prompts

- `prompts/retrieval_python.prompt` — owns the confidence gate (primary)

## Non-Goals

- Does not test that pricing is suppressed (trigger's job; pricing is a real,
  answerable question the product deliberately stays silent on upstream).
