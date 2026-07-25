# Issue #0 — PRD (the one `pdd-generate` runs on)

**Owner:** Lane 4
**Label:** `pdd-generate` — apply ONCE, before any other issue exists
**Title:** `[PRD] Live Answer Card MVP`

Copy everything below the line into the issue body.

---

# Live Answer Card MVP — Product Requirements Document

## Title

**Live Answer Card MVP**

### Project Overview

During a live sales call, when a prospect asks a technical question, a support
screen shows the answer as two or three large keywords within about three
seconds — and shows nothing at all when the system is not confident.

## Goals

- Remove the "let me check and get back to you" moment from technical sales calls
- Deliver an answer inside the ~3 second window before the rep must speak
- Ground every answer in the company's own product documents, with a traceable source
- Stay visibly silent when not confident, rather than guessing
- Run as a single Python process that can be demonstrated with no network
- Deploy to Render as a hosted web service, so the demo survives a dead laptop

### Why this shape

Sales calls already have two or three people on them. One talks; another has a
laptop open. This system runs on that second laptop. The speaker glances at it
and keeps talking — they never break eye contact to read a screen.

The screen shows keywords, not sentences. A paragraph must be read, parsed and
relayed, which is too slow. Two or three large words are glanced at and spoken.

## Key Features

### 1. Live transcription

**Description**: Capture call audio and convert it to complete utterances.

**Functionality**:

- Stream microphone audio to a realtime speech-to-text service over WebSocket
- Use voice-activity-based automatic commit to determine utterance boundaries
- Discard partial transcripts; emit only committed ones
- Return each utterance exactly once, never blocking the caller
- Reconnect automatically if the connection drops
- Label the speaker when available, otherwise report unknown

**Explicitly not required**: custom sentence-splitting logic. The transcription
service already determines segment boundaries via its commit strategy, and a
second splitting layer would only disagree with the first.

### 2. Fire decision

**Description**: Decide, for each utterance, whether the screen shows anything.

This is the core of the product. Reacting to every sentence turns the screen
into noise, which is worse than showing nothing at all.

**Four decisions, evaluated in order**:

1. Is this a question at all? Statements and back-channel ("mm-hmm", "right")
   never fire.
2. Is it technical or spec-related? Pricing, scheduling and small talk never
   fire, even when phrased as questions.
3. Has this already been answered on this call? Re-firing the same card makes
   the screen noise and the rep stops trusting it.
4. Is it phrased well enough for retrieval? If not, rewrite it into a clean
   question string.

**Functionality**:

- Resolve decisions 1 and 3 without a model call wherever possible, since most
  of a sales call is small talk and every avoided call is saved latency
- Classify with a fast model returning strict JSON
- Parse defensively; a malformed response produces no card rather than an error
- Track answered questions for the current call and detect re-asks phrased
  differently
- Expose per-utterance reasoning for tuning and explanation

**Optimisation target**: precision over recall. A missed question is a small
loss. A card firing during small talk destroys both the demo and the claim
behind it.

### 3. Grounded answer

**Description**: Turn a question into keyword card content drawn from product
documents.

**Functionality**:

- Ingest a small corpus of product documents into a local vector store
- Retrieve the passages most relevant to the question
- Generate 2–3 short keywords from the retrieved passages using a fast model
- The first keyword carries the answer; the rest are follow-up detail
- Return a one-or-two sentence detail string, revealed only on demand
- Return the source filename and page or section for every answer
- Return a confidence score between 0.0 and 1.0

**Confidence**: derived from both retrieval distance and the model's own
assessment. The derivation must be explainable in one sentence, because it will
be questioned during judging.

**Documents**: six markdown files in `corpus/`, describing Vantic, a fictional
AI infrastructure company with three products (Evals, Traces, Gateway). Because
the same term means different things per product — "retention" is 90 days on
Traces, 7 days on Gateway, and indefinite on Evals — retrieval must actually
discriminate rather than keyword-match, and confidence scores become meaningful
instead of uniformly high.

### 4. Keyword screen

**Description**: The support display. The only part of the system a human sees.

**Functionality**:

- Render 2–3 keywords at large size, readable from two seats away
- Render a designed empty state when confidence falls below 0.6
- Reveal detail and source when a keyword is selected; nothing else is
  interactive
- Dark background, high contrast

**The empty state is a designed screen, not a blank page.** It will be shown
deliberately during the demo to prove a decision layer exists, so it must look
intentional rather than like a page that failed to load.

### 5. Demo insurance

**Description**: Two independent fallbacks so a failure on stage is survivable.

**Functionality**:

- A typed-input path that calls the answer function directly, bypassing audio
  entirely, for use if the microphone fails
- A cache mode that replays saved responses for the demo questions with no
  network access at all, for use if venue wifi fails
- Per-cycle elapsed time printed in seconds, so the latency claim is measured
  rather than estimated

### 6. Deployment

**Description**: The app runs hosted on Render in addition to running locally.

**Functionality**:

- Deployed as a Render web service running `streamlit run app.py`
- Configuration supplied through Render environment variables, never committed
- Deploys triggered from the repository, so the hosted version tracks `main`
- The hosted instance defaults to typed-input mode, since the venue microphone
  is attached to a local machine rather than to the server

**Why it matters beyond deployment**: a live URL is the strongest demo insurance
we have. If the presenting laptop dies, the demo continues from any browser in
the room.

**To confirm on site**: whether the required Render surface is Workflows
specifically or a plain web service. Ask Render before treating this as done.

## Technical Constraints

These are requirements, not preferences. The system is a single local Python
process built in one day and demonstrated from one laptop.

- **Plain Python.** No web framework, no HTTP server, no REST API.
- **No frontend framework.** No React, no Next.js, no TypeScript, no JSX. The
  screen is Streamlit only.
- **Streamlit owns the entry point.** The application is a single Streamlit
  script, `app.py`, started with `streamlit run app.py`. Do not generate a
  `main.py` that imports Streamlit functions and calls them from an external
  loop — that inverts Streamlit's execution model and will not run.
- **No database.** State lives in memory and in a vector store directory
  bundled with the application. No SQL, no ORM, no migrations.
- **Runs unchanged locally and hosted.** No local-only absolute paths, no
  reliance on a display or a local microphone being present, and every
  configuration value readable from the environment.
- **No async and no class hierarchies** unless genuinely required. Threads are
  acceptable in the audio module for the WebSocket listener.
- **No authentication, no user accounts, no sessions.**
- Modules communicate by direct function call inside one process.
- Every module carries a `USE_MOCK` flag. When true it returns hardcoded sample
  data immediately and makes no network call. Mock implementations are written
  first and all tests must pass with no network access.
- No module function ever raises. Each wraps its body in try/except, logs with
  `print()`, and returns its defined empty value.
- Dependencies minimal and pinned.
- All credentials come from a `.env` file. No key is ever hardcoded, printed,
  or committed.
- Every network call has an explicit timeout.

## Module Interfaces

The system is five functions plus a loop. **These signatures and dictionary
keys are frozen** — four people build against them in parallel, so a change
made silently breaks three others.

```python
# audio
def get_utterance() -> dict:
    """{"text": str, "speaker": "prospect"|"rep"|"unknown", "ts": float}
    empty: {"text": "", "speaker": "unknown", "ts": 0.0}"""

# trigger
def should_fire(utterance: dict) -> dict:
    """{"fire": bool, "question": str, "reason": str}
    reason in {"technical", "smalltalk", "repeat", "not_a_question"}
    empty: {"fire": False, "question": "", "reason": "not_a_question"}"""

# retrieval
def answer(question: str) -> dict:
    """{"keywords": list[str], "detail": str, "source": str, "confidence": float}
    empty: {"keywords": [], "detail": "", "source": "", "confidence": 0.0}"""

# screen
def render(card: dict) -> None:
    """Draws the card. Below 0.6 confidence, draws the empty state instead."""

# model_client
def fast_complete(prompt: str, max_tokens: int = 200) -> str:
    """Provider-agnostic fast-model call. Returns "" on any error or timeout."""
```

### The application entry point

There is exactly one entry point, `app.py`, and it is a Streamlit application
started with `streamlit run app.py`. There is no separate `main.py`.

This matters because Streamlit owns its own execution model — it re-runs the
script top to bottom rather than being called from an external loop. A plain
`while` loop in a separate file calling `screen.render()` would not work. The
loop must live inside the Streamlit script.

`app.py` runs in one of two modes, selected in the sidebar:

**Live mode** — the polling loop, for the audio demo:

```python
placeholder = st.empty()
while st.session_state.running:
    u = audio.get_utterance()
    if not u["text"]:
        time.sleep(0.1)
        continue
    d = trigger.should_fire(u)
    if not d["fire"]:
        continue
    card = retrieval.answer(d["question"])
    with placeholder.container():
        screen.render(card)
```

**Typed mode** — no loop, standard Streamlit widgets, for the microphone-failure
fallback:

```python
q = st.text_input("Question")
if q:
    card = retrieval.answer(q)
    screen.render(card)
```

The two modes are mutually exclusive. Live mode blocks widget interaction while
the loop runs, which is expected and acceptable; the sidebar toggle stops the
loop before switching.

`screen.render(card)` is unchanged by this and draws into whatever Streamlit
container is active when it is called. It does not know or care which mode it
is running under.

Only `model_client` may import a model provider SDK. Every other module calls
`fast_complete()`.

## Data Contracts

```json
{
  "utterance": {
    "text": "Are you guys SOC 2 certified?",
    "speaker": "prospect",
    "ts": 252.4
  },
  "decision": {
    "fire": true,
    "question": "Are you SOC 2 certified?",
    "reason": "technical"
  },
  "card": {
    "keywords": ["SOC 2 — YES", "TYPE II", "NDA → REPORT"],
    "detail": "SOC 2 Type II, renewed March 2024 after an external audit.",
    "source": "security-overview.pdf p.4",
    "confidence": 0.91
  }
}
```

## Non-Functional Requirements

### Latency — the defining constraint

The window is about three seconds: the gap between a question landing and the
rep having to say something. An answer at two seconds saves the call. An answer
at six seconds is worthless, because the rep already stalled. Slow does not mean
"less good" here — it means the product does not exist.

| Stage | Budget |
|---|---|
| Microphone input to committed transcript | < 1000 ms |
| Fire decision, cheap-path rejection | < 50 ms |
| Fire decision, model-classified path | < 400 ms |
| Vector search | < 100 ms |
| Keyword generation | < 1400 ms |
| Screen render | < 100 ms |
| **End to end, question heard to card visible** | **< 3000 ms** |

Every model call carries an explicit timeout at or below its stage budget. A
timeout produces the empty state, never a wait.

### Reliability

- No module function raises under any input, including malformed upstream data
- The loop survives any single module misbehaving and continues to the next cycle
- Switching modes in the sidebar stops the loop cleanly rather than hanging
- A failed lookup is indistinguishable on screen from a deliberate silence —
  both render the empty state, which is a designed outcome rather than a fallback
- The full demo path runs with the network disconnected

### Observability

- Every module prints one line on entry and exit, including its inputs and the
  key output value, so a misbehaving module is identifiable within seconds
  during integration
- Per-cycle elapsed wall-clock time is printed in seconds and shown in the app

### Security

- No credential appears in source, logs, issues, or commits
- No real customer or personal documents are used; the corpus is fictional

## Environment

```
FAST_MODEL_PROVIDER=
FAST_MODEL_NAME=
FAST_MODEL_BASE_URL=
FAST_MODEL_API_KEY=

# optional secondary provider, same interface
FALLBACK_MODEL_NAME=
FALLBACK_MODEL_BASE_URL=
FALLBACK_MODEL_API_KEY=

ELEVENLABS_API_KEY=
```

The fast model provider is decided at build time based on available credits, so
no provider, model name or endpoint is hardcoded anywhere. Assume an
OpenAI-compatible chat completions endpoint unless configured otherwise, so that
changing providers is an environment edit rather than a code change.

If a secondary provider is configured, `model_client` falls back to it when the
primary times out or errors. Two providers configured means a single provider
outage or rate limit does not stop the demo. If the fallback is not configured,
behaviour is unchanged.

## User Stories

1. As a sales rep, I want a technical answer to appear before I have to speak,
   so that the call never stalls on "let me check."
2. As the teammate watching the support screen, I want two or three large words
   I can read at a glance, so that I can relay them without breaking the
   conversation's rhythm.
3. As a rep, I want the screen to stay blank during small talk, so that I keep
   trusting it when it does show something.
4. As a rep, I want to know which document an answer came from, so that I can
   stand behind what I just said.
5. As a presenter, I want the demo to survive a dead microphone or dead wifi,
   so that a venue problem does not become a product failure.

## Success Metrics

- End-to-end latency under 3 seconds at the 95th percentile
- Zero cards fired on small-talk utterances in the labelled test set
- At least 18 of 20 labelled test utterances classified correctly
- Every card displays a source
- The complete demo path runs with the network disconnected
- The app is reachable at a public URL and answers a typed question there

## Out of Scope

Not built in this version. Do not generate code, configuration, or dependencies
for any of these.

- User accounts, authentication, authorisation, sessions
- Any REST API of our own. Streamlit runs its own web server and that is
  expected; we do not build additional HTTP endpoints on top of it
- Any browser frontend framework — no React, Next.js, or TypeScript
- Any database, ORM, or schema migration
- Storing, recording, or persisting call audio
- Multi-user, multi-tenant, or concurrent call support
- CRM integration
- Analytics, dashboards, or reporting
- Speaker identity beyond a best-effort label
- Any language other than English

## Future Enhancements

- On-device models for privacy-sensitive deployment
- CRM integration so answers reflect the specific account
- Post-call summary of every question asked and how it was answered
- Rep-side feedback to improve retrieval over time
- Multilingual calls
