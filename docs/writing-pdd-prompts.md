# Writing PDD prompts

How to turn a GitHub issue into a `.prompt` file under `prompts/`, and the
rules every prompt in this repo follows. Read this before writing or editing
anything under `prompts/`.

## The one rule that matters

**The GitHub issues are NOT prompts.** Issues are written for the team: they
carry lane assignments, scheduling ("this unblocks Lane 4"), demo-risk notes
("a crashed screen in front of judges is fatal"), and prize strategy ("on
stage we show it on purpose, to prove a decision layer exists"). None of that
may reach the model. A code generator that knows about judges optimizes for
judges; one that only knows the behavioral contract optimizes for the
contract.

A prompt is the issue with the team stripped out and the contract kept in.

## Repo layout

```
context/
  project_preamble.prompt      # shared: product, frozen interfaces, code rules
prompts/
  _TEMPLATE_module_python.prompt
  audio_python.prompt          # Lane 2, mock utterance source
  retrieval_python.prompt      # reference conversion — copy its shape
  trigger_python.prompt        # Lane 3, converted from issue #10
  model_client_python.prompt   # Lane 3, converted from issue #10
  band_python.prompt           # Lane 3, converted from issue #5 (optional feature)
docs/
  writing-pdd-prompts.md       # this file
```

- Naming: `<module>_<language>.prompt`, e.g. `retrieval_python.prompt`. One
  prompt per module. A later real version **replaces** the mock prompt in
  place — same file, same interface — it does not get a new file.
- **One prompt per module, even when one issue covers two.** Issue #10 (Lane 3)
  specifies both `trigger.py` and `model_client.py`; it became two prompt
  files. The trigger prompt declares the one-way architectural relationship
  with `<pdd-dependency>model_client_python.prompt</pdd-dependency>`.
- Every prompt includes
  `<include>context/project_preamble.prompt</include>` after any leading
  `<pdd-*>` architecture metadata. The preamble owns the product description,
  the five frozen interfaces, and the code rules, so no prompt restates them
  and no two prompts can drift apart. If your PDD setup does not resolve
  `<include>`, paste the preamble's content after the metadata instead — but
  keep the single source of truth in `context/`.

## Converting an issue: keep / strip

Work section by section through the issue.

**Keep — this is the contract:**

| Issue section | Becomes |
| --- | --- |
| Goal (the functional sentence) | MODULE |
| Contract — frozen | INTERFACE — frozen |
| Acceptance criteria | BEHAVIOR (numbered, Given/When/Then) |
| Must not | MUST NOT |
| Validation + Done when | VALIDATION |
| Product decisions (0.6 threshold, ≤3 keywords, 3 s budget) | keep verbatim |
| Log-line formats | keep verbatim — the team greps for them |

**Strip — this is for humans:**

- Lane labels, titles like `[Lane 1]`, and "copy everything below the line"
  scaffolding
- Scheduling and dependency talk: "this unblocks Lane 4", "comes in a later
  issue" *as motivation* (the bare fact "mock only in this version" stays,
  because it constrains imports and network use)
- Demo, stage, and judge strategy of any kind
- Team-process rules ("I'll take it to the team", who owns which lane)
- Anything from `ignore-gameplan.context/` that is not a behavioral
  requirement

**Rewrite, don't copy, the borderline lines.** Example from the Lane 1 issue:

> "Given any other question, then EMPTY is returned — so the empty screen can
> be demonstrated."

"Demonstrated" is demo strategy. The prompt keeps the requirement and drops
the motive:

> "Given any other question, then EMPTY is returned — the empty state must be
> reachable."

Issue #10 has the sharpest examples. "This is the module the judges are
actually evaluating" and "the claim we are making on stage" were dropped
entirely. "mem0 is a hackathon sponsor" became a bare `USE_MEM0` flag
requirement. But "sponsor rate limits sometimes arrive late" was **not** just
deleted — its functional consequence ("swapping providers must be a `.env`
edit, not a code change") is a real constraint and stayed. Strip the motive,
keep the requirement it produced.

## Writing the BEHAVIOR section

- Every line is observable: *Given X, when Y, then Z*. If you cannot write a
  test that fails when the line is violated, cut the line. "Handles edge cases
  gracefully" makes generated code worse, not better.
- Specify product decisions; do **not** specify implementation choices (chunk
  size, embedding model, retry backoff). Ask the generator to explain those
  choices in the PR instead.
- Every module prompt ends its BEHAVIOR list with the two invariants: errors
  return EMPTY without raising, and one log line per call in the module's
  documented format.

## Frozen means frozen

The five signatures and their dict keys in the preamble are frozen. A prompt
never proposes renaming them, changing arguments, or adding/removing dict
keys. If you believe one is genuinely wrong, raise it with the team outside
the prompt — do not "fix" it in a prompt, because four modules are generated
against the same interfaces and a unilateral change breaks the other three.

## Reference conversion

[`prompts/retrieval_python.prompt`](../prompts/retrieval_python.prompt) is the
worked example, converted from
[`ignore-gameplan.context/lane1_mock_issue.md`](../ignore-gameplan.context/lane1_mock_issue.md).
Diff them to see the rule applied: the contract, criteria, must-nots, and
validation carried over nearly verbatim; the lane header, the "unblocks
Lane 4" motivation, and the demo phrasing did not.

## Checklist before committing a prompt

1. Starts with the preamble include; restates none of the preamble's content.
2. File is named `<module>_<language>.prompt` and covers exactly one module.
3. No lane numbers, scheduling, demo, judge, or prize language anywhere.
4. Every BEHAVIOR line is testable; no vague criteria survived.
5. Product decisions stated; implementation choices left open.
6. MUST NOT includes "must not raise" and the version's import restrictions.
7. VALIDATION gives a runnable command (`python <module>.py`) and observable
   done-conditions.
8. No secrets, keys, or `.env` contents — in the prompt or anywhere else.
