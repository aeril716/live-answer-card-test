<!-- pdd-story-contract derived-from-story="../story__retention_answer_matches_the_product.md" story-hash="auto" issue-ref="8" -->

# Contract: retention_answer_matches_the_product

## Covers

- prompts/ingest_python.prompt#R3: chunking preserves which product a passage describes
- prompts/retrieval_python.prompt#R3: source and detail come from the best passage

This is a cross-dev-unit story: retrieval can only return the right product's
number if ingestion kept the products distinguishable.

## Context / Fixtures

The corpus store is built from `corpus/`. The security overview retention
section (§3) states Traces retains 90 days, Gateway request logs 7 days, and
Evals indefinitely. `answer()` runs in real mode.

## Acceptance Criteria

1. Given the built store,
   when `answer("How long do you retain trace data?")` is called,
   then the card reflects the Traces retention (90 days) and is sourced to the
   retention section.

2. Given the built store,
   when `answer("How long does Gateway keep request logs?")` is called,
   then the card reflects the Gateway retention (7 days) and is sourced to the
   retention section.

3. Given both calls,
   then the two cards do not return the same product's number, and each has
   confidence at least 0.6.

## Oracle

- Both answers are sourced to `security-overview.md §3`.
- The Traces answer surfaces 90 days; the Gateway answer surfaces 7 days.
- The Gateway answer does not surface 90 days as its lead fact, and vice versa.
- Both confidences are at least 0.6.

## Non-Oracle

- Whether the card surfaces one product's branch or contrasts several does not
  matter, as long as the product asked about is the one answered.
- Exact keyword wording and the exact confidence value do not matter.

## Negative Cases

- A Gateway retention question must not return only the Traces number.

## Candidate Prompts

- `prompts/ingest_python.prompt` — product-preserving chunking (primary)
- `prompts/retrieval_python.prompt` — selects and phrases the passage (primary)

## Non-Goals

- Does not test the Evals-indefinite branch specifically (covered informally).
- Does not test repeat suppression across the two questions (trigger's job).
