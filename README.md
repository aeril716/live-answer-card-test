# Live Answer Card

A real-time assistant for live sales calls. When a prospect asks a technical
question ("Are you SOC 2 certified?"), it retrieves a grounded answer from the
company's docs and shows it on a second screen as two or three large keywords —
in about three seconds, before the rep has to speak. When it isn't confident, it
shows nothing on purpose: a wrong keyword is worse than a blank screen.

Built by four MSDS-AI students at a one-day hackathon.

## How this was built — Prompt-Driven Development (PDD)

The challenge was the *method*, not just the product. Under **PDD, prompts and
issue specs are the source of truth and the Python is generated from them** — so
the engineering work lives in the PRD, the interface contracts, the per-module
specs, and the corpus, plus the integration that makes it run as one product.
The `.py` files are the output of that work, not the work itself. Everything is
mock-first: it runs offline, so the demo survives a dead mic or venue wifi.

## Modules

- **`screen.py`** — renders the support card: up to three large keywords and
  their source. Below 0.6 confidence, or on a malformed card, it draws a
  deliberate empty state instead — the silence is designed, not a failure.
- **`audio.py`** — `get_utterance()` returns one committed utterance at a time.
  A microphone-free mock path drives the loop offline; the live path streams
  from ElevenLabs Scribe realtime and discards partial transcripts.
- **`trigger.py`** — `should_fire()`, the decision layer and the heart of the
  product. It rejects small talk, pricing, repeats, and non-questions, biased
  toward precision: a missed card is safer than one firing mid-conversation.
- **`retrieval.py` / `ingest.py`** — grounded keyword answers from the product
  corpus via ChromaDB, each with a confidence score and a traceable source, so
  every answer can be defended.
- **`model_client.py`** — one provider-agnostic fast-model entry point. Returns
  `""` on any timeout or error and retries once against a fallback provider, so
  a single model going down never stops the demo.

Every module runs offline with `USE_MOCK`, and returns its empty contract rather
than raising.

## Run it

Live: **[live-answer-card.onrender.com](https://live-answer-card.onrender.com)** — opens straight into the scripted live call ·
landing page: [live-answer-card-landing.onrender.com](https://live-answer-card-landing.onrender.com)

```sh
pip install -r requirements.txt
python ingest.py            # build the corpus vector store (once)
streamlit run app.py        # opens in Live mode and plays the mock call
pytest -q                   # offline test suite
```

Real microphone mode (local only): put `ELEVENLABS_API_KEY` and
`AUDIO_USE_MOCK=false` in `.env`, restart, and speak — the pipeline runs
mic → realtime STT → trigger → retrieval → card inside the ~3-second pause.

## Contributors & Roles

Roles reflect ownership of the PDD work — the specs, the corpus, the lane
implementations, and the integration that made the pieces run as one product.
Listed alphabetically.

| Contributor | Role & contribution |
|---|---|
| **Aeri** (`aeril716`) | Product & PDD lead. Authored the PRD, the frozen interface contracts, all six lane specs, the shared-context/guardrails, and the RAG corpus. Owned Lane 3 (trigger + model_client), integrated the lanes into `app.py`, and debugged across lanes. |
| **Erin** (`sohyunerinyang`) | Lane 2 — audio. Built `audio.py` with both the offline mock path and the ElevenLabs Scribe realtime transcription. Synced the demo screen recording to its audio track and prepared the anticipated audience Q&A for the presentation. |
| **Jin Ha Park** | Lane 4 — screen & deploy. Built the `screen.py` render layer and the Render deployment that gated all three main prizes, created the mockup website, and produced the final demo and presentation deck. |
| **Prashasti9** | Lane 1 — retrieval & ingestion. Owned `retrieval.py` and `ingest.py`, kicked off the PDD generation pipeline, and produced the video used on the mockup site. |

> In a prompt-driven workflow, the specifications and corpus *are* the
> engineering artifact; the generated code is their output. Implementation
> code (`app.py`, `retrieval.py`, `ingest.py`, `trigger.py`, and the test
> suite) was agent-generated from the prompts and specs above.
