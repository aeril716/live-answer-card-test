<!-- pdd-story-contract derived-from-story="../story__every_shown_card_names_its_source.md" story-hash="auto" issue-ref="8" -->

# Contract: every_shown_card_names_its_source

## Covers

- prompts/retrieval_python.prompt#R7: never keywords without a source
- prompts/retrieval_python.prompt#R1: the returned dict keeps the frozen keys

This is a negative story: it protects against an untraceable card.

## Context / Fixtures

`answer()` is called across a range of questions — answerable, unanswerable,
and small talk — in both mock and real mode.

## Acceptance Criteria

1. Given any question,
   when `answer()` returns a card whose `keywords` list is non-empty,
   then its `source` is a non-empty string.

2. Given any question,
   when `answer()` returns,
   then the result has exactly the keys `keywords`, `detail`, `source`,
   `confidence`.

## Oracle

- For every returned card: `keywords` non-empty implies `source` non-empty.
- The returned dict's key set is exactly the four frozen keys.

## Non-Oracle

- The specific source string does not matter here (a different story checks the
  SOC 2 source exactly).
- Keyword wording does not matter.

## Negative Cases

- Must never return non-empty `keywords` with an empty `source`.

## Candidate Prompts

- `prompts/retrieval_python.prompt` — owns the card shape (primary)

## Non-Goals

- Does not check confidence thresholds (a separate story does).
