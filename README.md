# live-answer-card-test

## Terminal support screen

`screen.py` provides `render(card)`, a dependency-free terminal preview of the
support card. Complete cards with confidence at least `0.6` display up to three
uppercase keywords and their source in a bordered box. Lower-confidence,
incomplete, or malformed cards display a deliberate bordered `-` empty state.

Run the four built-in examples with:

```sh
python screen.py
```

Each call also prints `[screen] in=conf=<confidence> out=<rendered|empty>` for
the end-to-end demo trace. Streamlit rendering is intentionally out of scope for
this version.

## Mock audio input

`audio.get_utterance()` provides deterministic, microphone-free input for the
application loop. With `USE_MOCK = True`, successive calls return four
hardcoded prospect utterances once each, in order, and then return:

```python
{"text": "", "speaker": "unknown", "ts": 0.0}
```

The mock performs no network or audio-device work. Run its six-call exhaustion
demo with:

```sh
python audio.py
```

Each call prints `[audio] out=<text>`.

## Decision layer

`trigger.should_fire(utterance)` decides whether an utterance should produce a
support card. It rejects rep speech, obvious non-questions, repeats, pricing,
scheduling, and small talk before returning:

```python
{"fire": bool, "question": str, "reason": str}
```

The trigger is deliberately biased toward precision: a missed card is safer
than an irrelevant card during small talk. Cheap checks run in the order
question → repeat → domain/rewrite. Prospect and unknown-speaker utterances are
classified by content; rep utterances never fire.

Call `trigger.reset_call()` at the start of each sales call. A question is
recorded when it fires, so it will not fire again during that call even if
retrieval or display later fails. Local similarity matching is the default;
optional mem0-backed matching is enabled by setting `USE_MEM0` to `1`, `true`,
`yes`, or `on` (case-insensitive). Missing, blank, or unrecognized values
default to `False`, so local memory remains the fail-safe.

`model_client.fast_complete(prompt, max_tokens=200)` is the
provider-independent fast-model entry point. It returns model text on success
and `""` on every timeout or error. Configure the primary endpoint with
`FAST_MODEL_*`. If every `FALLBACK_MODEL_*` value is set, a failed primary
attempt is followed by one fallback attempt. Each attempt has a 200 ms timeout,
SDK retries are disabled, and logs identify only the configured provider name.

Copy `.env.example` to `.env`, fill in the provider settings, and run the
offline tests:

```sh
pytest tests/test_model_client.py tests/test_trigger.py -q
```

The trigger test set runs without network access and requires at least 18/20
correct classifications with zero small-talk fires.
