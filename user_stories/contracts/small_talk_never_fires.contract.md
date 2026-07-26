<!-- pdd-story-contract derived-from-story="../story__small_talk_never_fires.md" story-hash="auto" issue-ref="10" -->

# Contract: small_talk_never_fires

## Covers

- prompts/trigger_python.prompt#2: pricing, scheduling, and small talk never fire
- prompts/trigger_python.prompt#11: zero fires for every small-talk case in the labelled set

This is a negative story: silence is the asserted outcome.

## Context / Fixtures

The labelled oracle `context/trigger_labelled_set.json` runs in order with
shared call state, mock mode, no network.

## Acceptance Criteria

1. Given the labelled call, when the weekend, pricing, deck, hiring, and
   scheduling lines are processed, then `fire` is False for every one.
2. Given any run of the full set, then the count of fired small-talk rows is
   exactly zero — independent of the overall accuracy score.

## Oracle

- `tests/test_trigger.py::test_hard_gate_zero_smalltalk_fires`
- `tests/test_trigger.py::test_oracle_accuracy_18_of_20`

## Non-Oracle

- Whether a small-talk line is rejected by the deny list or the classifier
  does not matter.

## Negative Cases

- Must not fire on a question-shaped non-technical line ("Are you guys hiring
  right now?").

## Candidate Prompts

- `prompts/trigger_python.prompt` — owns the decision layer (primary)
