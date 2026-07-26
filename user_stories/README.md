# User stories — the mold walls

Prompt-level acceptance stories for the whole system, following the two-file
split in the PDD prompting guide. They make the frozen contracts
**regeneration-safe molds**: a human reads and signs off the Story; the
contract holds the machine-checkable oracle; an executable test enforces it.

```
story__<name>.md                  human Story — one plain-language sentence, the source of truth
contracts/<name>.contract.md      Covers / Acceptance / Oracle / Non-Oracle / Negative Cases
```

**Edit the Story, not the contract.** Contracts are regenerated from the Story
plus the originating issue.

## The stories

| Story | Covers | Kind | Enforced by |
|---|---|---|---|
| `soc2_card_answers_with_source` | retrieval R3, R6, R4 | positive | `tests/test_retrieval.py::test_acceptance_questions_real_path`, `::test_soc2_exact_section_real_path` |
| `retention_answer_matches_the_product` | ingest R3, retrieval R3 | positive (cross-unit) | `tests/test_retrieval.py` retention cases, `tests/test_ingest.py::test_gateway_retention_prefers_security_section_3` |
| `screen_stays_blank_when_unsure` | retrieval R4, R8 | negative | `tests/test_retrieval.py::test_out_of_corpus_stays_blank_real_path`, `::test_answer_never_raises_on_internal_error` |
| `every_shown_card_names_its_source` | retrieval R7, R1 | negative | `tests/test_retrieval.py::test_never_a_card_with_empty_source`, `::_assert_shape` |
| `small_talk_never_fires` | trigger 2, 11 | negative | `tests/test_trigger.py::test_hard_gate_zero_smalltalk_fires`, `::test_oracle_accuracy_18_of_20` |
| `a_question_is_answered_only_once` | trigger 4, 5 | negative | `tests/test_trigger.py::test_repeat_resets_between_calls`, oracle rows 8/17 |
| `the_call_streams_in_as_utterances` | audio contract | positive | `python audio.py` demo, `tests/test_app.py::test_process_utterance_full_mock_loop_never_raises` |
| `the_rep_reads_three_words_not_sentences` | screen contract | positive | `tests/test_screen.py` (all cases) |

Rule references use the numbered `% Requirements` / `% Contract rules` of the
named prompt. Every MUST NOT rule is backed by a negative story and a negative
test.
