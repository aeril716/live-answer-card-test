<!-- pdd-story-contract derived-from-story="../story__a_question_is_answered_only_once.md" story-hash="auto" issue-ref="10" -->

# Contract: a_question_is_answered_only_once

## Covers

- prompts/trigger_python.prompt#4: a fired question is remembered immediately; reset_call() starts a new scope
- prompts/trigger_python.prompt#5: conservative lexical repeat matching

## Context / Fixtures

Labelled oracle rows 8 and 17 are re-asks of rows 4 and 14 in different words.
Crosstalk transcripts may wrap the same question in different surrounding text.

## Acceptance Criteria

1. Given "Are you SOC 2 certified?" fired earlier in the call,
   when "Are you SOC 2 compliant?" arrives, then `fire` is False with reason
   `repeat`.
2. Given the same extracted question inside two different chatter blobs,
   then the second occurrence reads `repeat`.
3. Given `reset_call()`, then the same question fires again — a new call is a
   clean slate.

## Oracle

- `tests/test_trigger.py::test_repeat_resets_between_calls`
- oracle rows 8 and 17 in `tests/test_trigger.py::test_oracle_accuracy_18_of_20`

## Non-Oracle

- The similarity metric internals (ratio vs word overlap) do not matter.

## Negative Cases

- Must not mark a *different* question about the same product as a repeat
  (oracle row 12: Gateway logs after Traces retention).

## Candidate Prompts

- `prompts/trigger_python.prompt` — owns repeat memory (primary)
