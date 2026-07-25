# Issue #1 — Lane 1 · Retrieval

**Owner:** Lane 1
**Label:** `pdd-change`
**Title:** `[Lane 1] retrieval.answer() — grounded keyword card from product docs`
**Post after** issue #0 has finished and the team has read `architecture.json`.

Copy everything below the line into the issue body.

---

## Goal

`retrieval.answer(question)` returns two or three glanceable keywords grounded
in our product documents, with a confidence score and a traceable source, in
under 1.5 seconds.

## Context

This module owns the confidence score and therefore owns the decision to show
nothing. The screen renders the empty state below 0.6, but the number itself is
mine, and I have to be able to defend it to a judge who asks "how do you know
it's 0.91?"

Keywords are read at a glance and spoken aloud immediately. `"SOC 2 — YES"` is a
keyword. `"We are SOC 2 Type II certified"` is a sentence and is useless — by
the time the rep has parsed it, the pause already happened. The first keyword
carries the actual answer; the rest are follow-up detail for when the prospect
digs.

Stack: ChromaDB `PersistentClient`, one collection, `add()` with documents and
metadatas, `query()` with `n_results`. Keyword generation goes through
`model_client.fast_complete()` — no provider SDK in this file. Source documents
live in `corpus/` — six markdown files for Vantic, a fictional AI infrastructure
company with three products: Evals, Traces and Gateway. The files are
company-overview, security-overview, sla, pricing, integrations and
gateway-spec. Sections are numbered so `source` can cite them precisely, e.g.
`security-overview.md §3`.

## Acceptance criteria

1. Given `USE_MOCK = True`, when `answer("anything")` is called, then it returns
   the mock card immediately with no network access.
2. Given the documents are ingested and `USE_MOCK = False`, when
   `answer("Are you SOC 2 certified?")` is called, then the returned `source`
   names the security document and `confidence` is at least 0.6.
3. Given a question with no supporting passage in the documents, when `answer()`
   is called, then `confidence` is below 0.6.
4. Given `answer()` returns a card, then `keywords` contains between 2 and 3
   items and each is at most 24 characters.
5. Given the model call times out or returns malformed JSON, when `answer()` is
   called, then it returns the EMPTY contract value and does not raise.
6. Given a separate `ingest.py` is run, then the ChromaDB collection is
   populated and the chunk size used is recorded in a comment explaining the
   choice.

## Must not

- Must not raise under any circumstance — catch and return EMPTY.
- Must not import a model provider SDK. Use `model_client.fast_complete()`.
- Must not return more than 3 keywords.
- Must not return a card without a populated `source` field. An answer we can't
  trace is an answer we can't defend.
- Must not exceed a 2-second timeout on the model call.

## Evidence

Expected shape:

```python
{
    "keywords": ["SOC 2 — YES", "TYPE II", "NDA → REPORT"],
    "detail": "SOC 2 Type II, renewed March 2026 after an external audit.",
    "source": "security-overview.md §1.1",
    "confidence": 0.91
}
```

## Validation

- Test: `pytest tests/test_retrieval.py -q`
- Include a script that runs the test set in `corpus/README.md` — 8 answerable,
  3 not, plus 4 that diverge by product — printing question / keywords /
  confidence, so the 0.6 threshold is tuned against real numbers rather than
  guessed.
- Manual: type a question into the Lane 4 fallback box and confirm the right
  passage comes back.

## Also explain, in the PR description

How the confidence score is derived — retrieval distance, the model's own
self-assessment, or a combination — how the two are weighted, and where it is
weakest. I need to say this out loud on stage without hand-waving.

## Done when

- Mock version works and Lane 4 is unblocked
- `ingest.py` populates ChromaDB and the chunk size choice is explained
- All six acceptance criteria have passing tests
- Criterion 3 (the unanswerable question) has an explicit negative test
