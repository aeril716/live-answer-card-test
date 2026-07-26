<!-- pdd-story-contract derived-from-story="../story__the_rep_reads_three_words_not_sentences.md" story-hash="auto" issue-ref="4" -->

# Contract: the_rep_reads_three_words_not_sentences

## Covers

- prompts/screen_python.prompt: at most three keywords render; below 0.6
  confidence the designed empty state renders; malformed cards never raise

## Context / Fixtures

`screen.render()` draws the four demonstration cases: a full card, a card at
confidence 0.4, an empty dict, and a card with five keywords.

## Acceptance Criteria

1. Given a card with five keywords, then only three render.
2. Given confidence below 0.6, then the empty state renders — visibly
   deliberate, never an error.
3. Given an empty dict, then the empty state renders and nothing raises.

## Oracle

- `tests/test_screen.py` (all cases)

## Non-Oracle

- Exact box-drawing characters and spacing do not matter.

## Negative Cases

- Must not render more than three keywords; must not look like a crash.

## Candidate Prompts

- `prompts/screen_python.prompt` — owns the renderer (primary)
