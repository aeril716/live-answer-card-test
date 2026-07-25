# Demo script — Live Answer Card

Two people role-play a sales call. One is the **prospect** (P), one is the
**rep** (R). A third person can narrate the close, or R can do it.

Target runtime: **3 minutes.** Read the lines as written. The labels below are
what the system should decide — if a line changes, the demo's claim changes with
it.

---

## Before you start

- [ ] Screen visible to judges, dark mode, empty state showing
- [ ] Mode set to **live** in the sidebar (or **typed** if the mic is down)
- [ ] `demo_cache.json` present, `USE_CACHE` ready to flip if wifi dies
- [ ] Per-cycle timing visible somewhere on screen — the latency claim needs to
      be seen, not asserted
- [ ] One rehearsal done end to end, alone, on the actual demo laptop

---

## The script

### Beat 1 — the card fires

> **P:** So before we go further, I have to ask the compliance question.
> Are you SOC 2 certified?

*Screen: card fires.* Expected keywords along the lines of `SOC 2 — YES`,
`TYPE II`, `NDA → REPORT`, sourced to `security-overview.md §1.1`.

> **R:** *(glancing, not reading)* Yes — SOC 2 Type II. Happy to share the
> report once we have an NDA in place.

R must not lean toward the screen. The whole product argument is that the answer
is glanceable. Leaning in on stage undoes it.

---

### Beat 2 — a second question, a different answer

> **P:** Good. And how long do you retain trace data?

*Screen: card updates.* Expected: 90 days, sourced to the Traces section.

> **R:** Ninety days on Traces.

---

### Beat 3 — the same question, a different product

> **P:** Wait — what about Gateway? How long does it keep logs?

*Screen: card updates again.* Expected: 7 days.

> **R:** Seven days on Gateway. Different retention per product.

**This is the strongest beat and it looks like the weakest.** The words are
almost identical to beat 2 — "how long", "keep"/"retain", "logs"/"data" — but
the answer is different because the product is different. Retrieval had to
discriminate rather than keyword-match, and the repeat detector had to *not*
suppress it. Say so out loud:

> **R (to the room):** Same words, different product, different answer. That's
> retrieval discriminating, not string matching.

---

### Beat 4 — the screen stays empty, on purpose

> **P:** Nice. Anyway, how was your weekend? Did you get out at all?

*Screen: **nothing**. The empty state holds.*

**Pause here. Three full seconds.** Let the judges look at a blank screen and
register that it is designed rather than broken. This beat is the only direct
evidence that a decision layer exists — every other beat is equally explainable
by "they called an LLM on every sentence."

> **R (to the room):** That was a question. It just wasn't ours to answer. The
> system decided not to speak.

---

### Beat 5 — close on the design point

> **R:** Three things are happening here. It answers inside the three-second
> window before I'd have to stall. It shows keywords, not paragraphs — I glance
> and I speak, I never read. And it stays quiet when it should, which is why I
> trust it when it doesn't.

---

## Optional beat — the repeat

Insert between beats 3 and 4 if the timing allows. Cut it first if you are over.

> **P:** Sorry, remind me — are you SOC 2 compliant?

*Screen: **nothing**. Reason: repeat, already answered.*

> **R:** It already answered that one. Firing the same card twice is how the
> screen becomes noise.

Two different reasons for silence in one demo is a stronger claim than one. But
it is also the beat most likely to misfire during rehearsal, so treat it as a
bonus rather than a load-bearing part of the run.

---

## Microphone / transcription check

Run this **before** the demo, not during. It exercises Lane 2 alone.

Speak each line at normal call volume, from the presenting seat, with the room
as noisy as it will actually be:

1. "Are you SOC 2 certified?"
2. "How long do you retain trace data?"
3. "Wait — what about Gateway? How long does it keep logs?"
4. "Anyway, how was your weekend?"

What to watch for:

| Check | Passing looks like |
|---|---|
| Latency | text appears within about a second of finishing the sentence |
| Committed only | no half-sentences flicker and get replaced |
| One-shot delivery | each line appears exactly once, never twice |
| Boundaries | line 3 arrives as one utterance, not split at the dash |
| Reconnect | unplug and replug the mic — the loop keeps running, no crash |

If line 3 splits into two utterances, that is the API's commit boundary doing
its job, not a bug — but check that both halves are handled sanely, because the
second half carries the actual question.

If the room is loud enough that lines drop, that is the known Lane 2 risk. The
fallback is typed mode: same script, same lines, R types them instead. Practice
the switch once so it looks deliberate.

---

## Things that break this demo

**Improvising the small-talk line.** Beat 4 has to be genuinely non-technical.
"How was your weekend, did you get through that security review?" fires the card
and destroys the beat live. Read the line as written.

**Filling the silence.** The instinct at beat 4 is to keep talking because the
screen is blank. Don't. The blank screen is the point, and it needs air.

**Reading the screen aloud.** R relays the answer in their own words. Reading
"SOC 2 dash YES" out loud makes it look like a teleprompter instead of a glance.

**Changing a question string.** The three demo questions are cached in
`demo_cache.json` by exact text. Reword one and the offline path stops working
right when you need it.
