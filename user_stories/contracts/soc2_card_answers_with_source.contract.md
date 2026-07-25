<!-- pdd-story-contract derived-from-story="../story__soc2_card_answers_with_source.md" story-hash="auto" issue-ref="8" -->

# Contract: soc2_card_answers_with_source

## Covers

- prompts/retrieval_python.prompt#R3: source from the best retrieved passage
- prompts/retrieval_python.prompt#R6: at most three grounded keywords, answer first
- prompts/retrieval_python.prompt#R4: confidence at least 0.6 to show a card

## Context / Fixtures

The corpus store is built from `corpus/`. The security overview states SOC 2
Type II in §1.1. `answer()` runs in real mode (searching the store).

## Acceptance Criteria

1. Given the built store,
   when `answer("Are you SOC 2 certified?")` is called,
   then the returned `source` is `security-overview.md §1.1`.

2. Given the same call,
   then `confidence` is at least 0.6 and the card has between one and three
   keywords.

3. Given the same call,
   then every keyword is grounded in the retrieved passage and the first
   keyword carries the answer.

## Oracle

- `source` equals `security-overview.md §1.1`.
- `confidence` is at least 0.6.
- `1 <= len(keywords) <= 3`.
- Each keyword's content words appear in the retrieved passage.

## Non-Oracle

- The exact keyword wording does not matter (model phrasing or heading-derived).
- The exact confidence value above 0.6 does not matter.
- Private helper names and internal ordering do not matter.

## Negative Cases

(Empty — positive story.)

## Candidate Prompts

- `prompts/retrieval_python.prompt` — owns `answer()` (primary)
- `prompts/ingest_python.prompt` — supplies the `source` metadata (related)

## Non-Goals

- Does not test whether the question should fire (trigger's job).
- Does not test keyword rendering on the screen.
