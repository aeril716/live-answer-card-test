# Issue #4 — Lane 4 · Screen and demo

**Owner:** Lane 4 (also the person who runs `pdd-generate` on issue #0)
**Label:** `pdd-change`
**Title:** `[Lane 4] app.py + screen.render() — the thing judges look at`
**Post after** issue #0 has finished and the team has read `architecture.json`.

Copy everything below the line into the issue body.

---

## Goal

A support screen showing two or three enormous keywords, a designed empty state,
and two independent fallbacks that keep the demo alive if the microphone or the
venue wifi dies.

## Context

This is the only part of the system the judges actually see. Everything else is
inference.

`app.py` came out of issue #0 and I own it from here — the Streamlit entry
point, the polling loop, the mode toggle, the per-cycle timing, and the
guarantee that a malformed return from any module doesn't kill the app.

There is no `main.py`. Streamlit re-runs its script top to bottom rather than
being driven by an external loop, so the loop lives inside `app.py` and the app
is started with `streamlit run app.py`.

The screen is glanced at, not read. If someone has to lean in, the design
failed. Assume the judges are watching a projected screen from across a room,
not a laptop at arm's length.

The empty state matters more than it looks. On stage we will deliberately say
something non-technical and let the screen stay blank, to prove there's a
decision layer rather than an LLM firing at every sentence. So the empty state
has to look designed and intentional, not like a page that failed to load.

## Acceptance criteria

1. Given a hardcoded card dict, when the screen runs, then two or three
   keywords render at large size with no other modules running.
2. Given a card with `confidence` below 0.6, when `render()` is called, then the
   empty state renders instead of the card.
3. Given a malformed or partial card dict, when `render()` is called, then the
   empty state renders and no exception surfaces.
4. Given a keyword is tapped, then the `detail` and `source` become visible.
   Nothing else on the screen is clickable.
5. Given the typed-input fallback, when a question is typed and submitted, then
   `retrieval.answer()` is called directly and the resulting card renders,
   bypassing audio entirely. This is also the mode the hosted deployment runs
   in, since the server has no microphone.
6. Given `USE_CACHE = True` and `demo_cache.json` exists, when the three demo
   questions are asked, then the saved responses replay with no network access
   at all.
7. Given the live loop completes one cycle, then the elapsed wall-clock time for
   that cycle is printed and displayed in the app.
8. Given the sidebar mode is switched from live to typed, then the loop stops
   cleanly and the typed input becomes interactive.
9. Given the app is deployed to Render, when the public URL is opened, then
   typed-input mode loads and answers a question.
10. Given no microphone is available, when the app starts, then it defaults to
    typed mode and does not error.

## Must not

- Must not render more than three keywords.
- Must not raise — a malformed card renders the empty state.
- Must not let the loop terminate because a module returned something
  unexpected. Log and continue to the next cycle.
- Must not generate a separate `main.py` that imports Streamlit and calls it
  from an external loop. Streamlit owns the entry point.
- Must not make the empty state look like an error, a spinner, or a blank page.
- Must not require a microphone or a network connection to demonstrate.

## Design constraints

- Dark background, high contrast, readable from two seats away
- Keywords at the largest size the layout allows — glanceable, not readable
- Never more than three
- Only keywords are interactive

Use Streamlit unless there's a strong reason not to. Say which was chosen and
why in the PR description.

## Validation

- Test: `pytest tests/test_screen.py -q` — criteria 2 and 3 especially, since
  those are the two that save us in front of judges.
- Manual: `streamlit run app.py` with all modules mocked; confirm a full cycle
  renders a card, then confirm a mock small-talk line leaves the screen empty.
- Manual: pull the wifi and confirm the cached path still renders.

## Also deliver

A three-minute demo script with exact lines for two people role-playing a sales
call:

1. Prospect asks the SOC 2 question — card fires, rep answers without pausing
2. Prospect follows up with a narrower version — card updates
3. Someone says something non-technical — **screen stays empty, on purpose**
4. Close on the design point: keywords, not paragraphs

Step 3 carries more weight than it looks. Showing the system stay quiet is the
only direct evidence that a decision layer exists.

## Done when

- The card renders from a fake JSON payload with no other modules running
- `app.py` completes full cycles against all four mocks in live mode
- The typed fallback works with the microphone unplugged
- `demo_cache.json` exists and the cached path runs with wifi off
- The app is live on a Render URL, and someone other than Lane 4 has opened it
  on their own laptop and gotten an answer
- The demo script is written and one person has rehearsed it start to finish
  alone, on the actual demo laptop
