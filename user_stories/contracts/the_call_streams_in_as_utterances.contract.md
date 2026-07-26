<!-- pdd-story-contract derived-from-story="../story__the_call_streams_in_as_utterances.md" story-hash="auto" issue-ref="16" -->

# Contract: the_call_streams_in_as_utterances

## Covers

- prompts/audio_python.prompt: frozen utterance contract, non-blocking return,
  EMPTY after exhaustion, no raise

## Context / Fixtures

Mock mode replays the scripted four-utterance call with no network and no
microphone; the real path feeds the same contract from streaming transcripts.

## Acceptance Criteria

1. Given repeated calls, then each scripted utterance is returned exactly once,
   in order, with `ts` increasing.
2. Given the list is exhausted, then EMPTY is returned on every later call.
3. Given any call, then `get_utterance()` returns immediately — it never
   blocks the polling loop.

## Oracle

- `python audio.py` six-call demonstration
- `tests/test_app.py::test_process_utterance_full_mock_loop_never_raises`

## Non-Oracle

- The internal queue/thread mechanics of the real path do not matter.

## Negative Cases

- Must not return the same utterance twice; must not raise.

## Candidate Prompts

- `prompts/audio_python.prompt` — owns the utterance source (primary)
