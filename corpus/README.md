# Demo corpus — Vantic

Six documents for a fictional AI infrastructure company with three products.
Fictional on purpose: no real company's docs, no real customer data, which also
answers the privacy question before a judge asks it.

Why this industry: the judges are AI people. They already know the objections in
this market — SOC 2, data retention, "do you train on my data," self-hosting. So
the sales scenario lands in about two seconds without setup from us.

```
company-overview.md    the three products, deployment matrix
security-overview.md   certifications, data handling, retention, regions
sla.md                 uptime, credits, support response, maintenance
pricing.md             per-product pricing, overage, spend caps
integrations.md        SDKs, standards, frameworks, CI, export
gateway-spec.md        latency, caching, routing, limits
```

Sections are numbered so `source` can be specific: `security-overview.md §3`.

**The three products:** Evals (offline evaluation, CI gates), Traces (production
observability), Gateway (inference proxy).

---

## Why three products instead of one

A single-product corpus makes retrieval trivial — "SOC 2" appears in exactly one
place, every method finds it, and every confidence score comes back around 0.9.
A confidence number that is always high is not a measurement, and there is
nothing to tune the 0.6 threshold against.

Three products means the same word means different things in different places,
which is what forces retrieval to actually discriminate.

### Planted distractors

| Trap | Where |
|---|---|
| "Retention" means three different things | security §3 |
| ISO 27001 covers Evals and Traces but **not** Gateway | security §1.2 |
| Self-hosting: Traces and Gateway yes, Evals no | overview §4 |
| Air-gapped: Traces only — Gateway *cannot* | overview §4, gateway §6 |
| Uptime differs per product (99.5 / 99.9 / 99.95) | sla §1 |
| Customer-managed keys: not on Gateway in cloud | security §4 |
| PII redaction implemented differently per product | security §5 |
| EU region: Traces and Gateway only | security §7 |
| **"Response time"** — SLA support ticket vs Gateway added latency | sla §3, gateway §2 |
| Spend cap: blocks on Traces, holds on Evals, **alerts only** on Gateway | pricing §4 |

The last two are the good ones. "What's your response time?" is genuinely
ambiguous — one answer is 1 hour and the other is 11 ms, and they live in
different documents. If the system picks one silently, that's worth knowing.

---

## Lane 1 · Test set

**Should return high confidence:**

| # | Question | Lives in |
|---|---|---|
| 1 | Are you SOC 2 certified? | security §1.1 |
| 2 | Do you train models on our data? | security §2 |
| 3 | How long does Gateway keep request logs? | security §3 |
| 4 | Can we self-host Traces? | overview §4 |
| 5 | Do you support OpenTelemetry? | integrations §2 |
| 6 | What's the uptime commitment for Gateway? | sla §1 |
| 7 | How much latency does the proxy add on a cache hit? | gateway §2 |
| 8 | Are you ISO 27001 certified? | security §1.2 |

Question 8 is a trap on purpose. The honest answer is "yes for two products, not
for Gateway" — not a flat yes. A card reading `ISO 27001 — YES` is wrong even
though it will feel right.

**Should return low confidence (not in the corpus):**

| # | Question | Why |
|---|---|---|
| 9 | Do you have a Databricks connector? | not mentioned, and integrations §8 explicitly says absence ≠ unsupported |
| 10 | Who is your CEO? | no company-info document exists |
| 11 | What's your carbon footprint? | out of scope entirely |

Question 9 is the interesting one. The honest answer is "unknown," not "no." If
the system confidently says no, the confidence score is measuring the wrong
thing.

**Answers that diverge by product — the good demo material:**

| Question | Correct behaviour |
|---|---|
| How long do you retain data? | Surface that it differs: Traces 90d, Gateway 7d, Evals indefinite |
| What's your uptime SLA? | Differs per product |
| Can we bring our own encryption keys? | Yes, except Gateway in cloud mode |
| What's your response time? | Genuinely ambiguous — support ticket or proxy latency |

Getting a divergent answer to surface both branches would be excellent. Getting
one branch is acceptable and still correct. Getting one branch **while sounding
certain** is the failure worth catching.

---

## Lane 3 · Utterances that must NOT fire

| Utterance | Correct reason |
|---|---|
| How much is the Team plan? | `smalltalk` — pricing excluded by design |
| Could we get on a call Thursday? | `smalltalk` — scheduling |
| Right, mm-hmm, got it | `not_a_question` — back-channel |
| So how was your weekend? | `smalltalk` |
| Are you SOC 2 compliant? *(reworded re-ask)* | `repeat` |

The pricing one matters most. It is a real, answerable, document-backed question
that we deliberately stay silent on, because pricing is the rep's conversation to
have. If the card fires on pricing, the "we decide" claim weakens.

---

## Demo script (3 minutes)

Two laptops side by side: the call, and the support screen.

**Beat 1 — the moment the product exists for**

> **Prospect:** "Before we go further — are you SOC 2 certified?"

Card: `SOC 2 — YES` / `TYPE II` / `NDA → REPORT`

The rep answers without pausing. Say out loud that this is the sentence that
normally becomes "let me check and get back to you."

**Beat 2 — it holds up under a follow-up**

> **Prospect:** "Type I or Type II? And when was it last renewed?"

Card: `TYPE II` / `RENEWED MAR 2026` / `ANNUAL AUDIT`

**Beat 3 — a hard question with an honest answer**

> **Prospect:** "We handle patient data. Can you sign a BAA?"

Card: `HIPAA — NO BAA` / `SELF-HOST TRACES` / `PHI STAYS OUT`

Worth more than beat 1. The system surfaces a *no* clearly enough that the rep
can say it without flinching, and points at the workaround. It shows the system
is grounded rather than agreeable.

**Beat 4 — the restraint, on purpose**

> **Prospect:** "Makes sense. Anyway, how was your weekend?"

The screen shows the designed empty state: a bordered box containing `-`. Hold
it and let people see that the silence is deliberate.

> "That's the part we actually built. Answering is the easy half — deciding when
> not to answer is what keeps a rep trusting the screen."

**Beat 5 — close**

Keywords, not paragraphs. Under three seconds or it doesn't exist. One sentence
on breadth: the corpus is swappable, so the same pipeline runs on an industrial
equipment spec sheet with no code change.

**Optional, only if everything above is solid at 16:00**

Swap the corpus to the PDD documentation and ask "what's the best prompt
engineering company?" as a closing joke. Do not build this before the main demo
rehearses cleanly twice.
