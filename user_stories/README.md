# User stories — the retrieval mold walls

Prompt-level acceptance tests for Lane 1 (retrieval), following the two-file
split in the PDD prompting guide. They make the frozen retrieval contract a
**regeneration-safe mold**: a human reads and signs off the Story; the contract
holds the machine-checkable oracle; an executable test enforces it.

```
story__<name>.md                  human Story — one plain-language sentence, the source of truth
contracts/<name>.contract.md      Covers / Acceptance / Oracle / Non-Oracle / Negative Cases
```

**Edit the Story, not the contract.** The contract is regenerated from the
Story plus the originating issue (#8).

## The stories

| Story | Covers | Kind | Enforced by |
|---|---|---|---|
| `soc2_card_answers_with_source` | retrieval R3, R6, R4 | positive | `tests/test_retrieval.py::test_acceptance_questions_real_path`, `::test_soc2_exact_section_real_path` |
| `retention_answer_matches_the_product` | ingest R3, retrieval R3 | positive (cross-unit) | `tests/test_retrieval.py` retention cases, `tests/test_ingest.py::test_gateway_retention_prefers_security_section_3` |
| `screen_stays_blank_when_unsure` | retrieval R4, R8 | negative | `tests/test_retrieval.py::test_out_of_corpus_stays_blank_real_path`, `::test_answer_never_raises_on_internal_error` |
| `every_shown_card_names_its_source` | retrieval R7, R1 | negative | `tests/test_retrieval.py::test_never_a_card_with_empty_source`, `::_assert_shape` |

Rule IDs (`R<n>`) refer to the `% Contract rules` section of the named prompt.
Every MUST NOT rule (R7, R8) is backed by a negative story and a negative test.
