# Issue #2 — Lane 2 · Audio

**Owner:** Lane 2
**Label:** `pdd-change`
**Title:** `[Lane 2] audio.get_utterance() — streaming transcription via ElevenLabs Scribe v2 Realtime`
**Post after** issue #0 has finished and the team has read `architecture.json`.

Copy everything below the line into the issue body.

---

## Goal

`audio.get_utterance()` returns one complete, committed utterance at a time from
live microphone audio, in under a second, without ever blocking the main loop.

## Context

Everything downstream shares a three-second budget and this module spends the
first slice of it.

The API is **ElevenLabs Scribe v2 Realtime**. It is a WebSocket streaming
speech-to-text service, roughly 150ms latency. Audio goes up as
`input_audio_chunk` messages. Results come back in two forms: **partial**
transcripts while someone is still speaking, and **committed** transcripts once
a speech segment is complete. Commit strategy can be manual or VAD-based
automatic.

This shapes the whole module:

- Use **VAD-based automatic commit**.
- **Discard every partial transcript.** Only committed transcripts leave here.
- A committed transcript **is** the utterance boundary. Do not write custom
  sentence-splitting logic on top of it — the API already made that decision,
  and a second layer of splitting on top of it will only disagree with the
  first one.

So the WebSocket handler runs on its own thread and fills a thread-safe queue
with committed transcripts. `get_utterance()` pops from that queue and returns
EMPTY immediately when the queue is empty.

Speaker labels are optional. If diarization is slow or unreliable, return
`"unknown"` — the trigger lane copes fine without it. `ts` is seconds since the
call started, not a wall-clock timestamp.

## Acceptance criteria

1. Given `USE_MOCK = True`, when `get_utterance()` is called repeatedly, then it
   replays a hardcoded list of utterances on a timer with no network access.
2. Given the queue is empty, when `get_utterance()` is called, then it returns
   EMPTY immediately and does not block.
3. Given a partial transcript arrives from the WebSocket, then it is discarded
   and never returned by `get_utterance()`.
4. Given a committed transcript arrives, then a later `get_utterance()` call
   returns it exactly once and never returns it again.
5. Given the WebSocket connection drops, then the client reconnects
   automatically and the module keeps returning EMPTY meanwhile rather than
   raising.
6. Given a benchmark flag is enabled, then the module measures and prints
   microphone-input to returned-text latency in milliseconds.

## Must not

- Must not raise under any circumstance — catch and return EMPTY.
- Must not block the calling thread waiting for speech.
- Must not return partial transcripts.
- Must not return the same utterance twice.
- Must not implement custom sentence-boundary detection.

## Evidence

Expected shape:

```python
{"text": "Are you guys SOC 2 certified?", "speaker": "prospect", "ts": 252.4}
```

## Validation

- Test: `pytest tests/test_audio.py -q` — passes with no microphone and no
  network, using mock mode and a fake queue.
- Manual: speak into the laptop mic, confirm text appears within a second.

## Also answer, in the PR description

The demo-day risk this lane owns is venue noise, crosstalk, and a dying
microphone. Assume a loud room with four other teams demoing within earshot.
What breaks first, and what is the fallback?

## Done when

- Mock version works and `app.py` runs the loop without a microphone
- Real WebSocket transcription works on the demo laptop, in a noisy room
- A measured latency number exists that can go on a slide
- Criteria 2 and 3 have explicit tests — non-blocking, and no partials leak
