# SHARED CONTEXT — paste this first, every time

Anyone using Claude, Cursor, ChatGPT or anything else to help with their lane:
**paste the block below before your question.** Every time, in every new chat.

It exists so that four people asking four different AIs don't end up with four
subtly different systems.

The PRD (`issue_0_PRD.md`) is a different thing — that goes into one GitHub
issue, once, and only Lane 4 posts it.

---

```
I'm at a one-day hackathon with a team of four. Read this before answering.

WHAT WE'RE BUILDING — "Live Answer Card"
A sales call is happening. A prospect asks a technical question ("Are you SOC 2
certified?"). The rep can't answer from memory, so they stall: "let me check and
get back to you." That sentence loses deals.

Our system listens to the call. When it hears a technical question it can answer
from the company's product docs, it shows the answer on a SECOND laptop — the
one a teammate has open — as two or three large keywords the rep can glance at
and say out loud. Not sentences. Keywords.

TWO CONSTRAINTS THAT DECIDE EVERYTHING
1. SPEED. About 3 seconds, the gap before the rep has to say something. An
   answer at 2s saves the call; at 6s it's worthless because they already
   stalled. Slow doesn't mean worse here, it means the product doesn't exist.
2. SILENCE. The system shows nothing unless it's confident. Small talk, pricing,
   scheduling, anything it can't answer well produces an empty screen. A wrong
   keyword is much worse than a blank one. Silence is designed, not a failure.

THE FIVE FROZEN FUNCTIONS
    audio.get_utterance() -> dict
        {"text": str, "speaker": "prospect"|"rep"|"unknown", "ts": float}

    trigger.should_fire(utterance: dict) -> dict
        {"fire": bool, "question": str, "reason": str}
        reason in {"technical","smalltalk","repeat","not_a_question"}

    retrieval.answer(question: str) -> dict
        {"keywords": list[str], "detail": str, "source": str, "confidence": float}

    screen.render(card: dict) -> None
        draws the card; below 0.6 confidence draws the designed empty state

    model_client.fast_complete(prompt: str, max_tokens: int = 200) -> str
        provider-agnostic; returns "" on any error or timeout

Entry point is app.py, a Streamlit script that owns the polling loop. There is no
main.py — Streamlit re-runs its script rather than being driven from outside.

*** THESE SIGNATURES AND DICT KEYS ARE FROZEN. ***
Do not propose renaming them, changing arguments, or adding/removing dict keys,
even if you can see a cleaner design. Four people are building against them in
parallel and a change breaks three of them. If you think one is genuinely wrong,
say so in one sentence and stop — I'll take it to the team.

RULES FOR ANY CODE OR ISSUE TEXT YOU HELP ME WITH
1. A lane function NEVER raises. try/except, print the error, return the empty
   version of the contract. A crashed screen in front of judges is fatal; an
   empty screen is a state we designed.
2. Every module has USE_MOCK at the top. When True it returns hardcoded data and
   touches no network. Mocks come first, and every test passes offline.
3. Every module prints one line on entry and exit with its inputs and key output.
4. Plain Python. No web framework beyond Streamlit, no async, no class
   hierarchies, no abstractions "for later." We throw this away tonight.
5. Every network call has an explicit timeout at or under its latency budget.
6. Keys live in .env. Never hardcode, never print, never put one in example code.

HOW WE WORK — this is a Prompt Driven Development hackathon
Prompt files and GitHub issues are the source of truth. Python is generated from
them by the PDD tool. So:

- Help me write and sharpen ISSUES. Do not write implementation code for me to
  paste into the repo — that leaves no issue-to-PR trail, and the trail is what
  we're judged on.
- Throwaway code to answer a question is fine ("what shape does this API
  actually return?"). I'll learn the answer, discard the code, and write the
  finding into the issue as a constraint.
- If I ask you to write production code, remind me once, then do whichever I
  confirm.

WRITING ISSUES — what good looks like
Sections: Goal / Context / Acceptance criteria / Must not / Validation / Done
when. Acceptance criteria are observable: "Given X, when Y, then Z." If I can't
write a test that fails when a criterion is violated, cut it — vague
requirements like "handles edge cases gracefully" make the generated code worse,
not better.

Specify product decisions (the 0.6 threshold, 2-3 keywords, the 3-second
budget). Don't specify implementation choices (chunk size, embedding model,
retry backoff) — ask the tool to explain those instead.

Be concise and concrete. Push back if something I've asked for is a bad idea.
```

---

## Quick rules, for when you don't have the block handy

- Don't let any AI change the five function signatures
- Don't paste generated code into the repo — edit the issue and re-run instead
- Don't paste an API key anywhere an AI or the repo can see it
- Cut any requirement you can't write a test for
