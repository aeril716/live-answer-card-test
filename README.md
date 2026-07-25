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
