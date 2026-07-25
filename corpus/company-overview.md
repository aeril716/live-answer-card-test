# Vantic — Product Overview

> Fictional company. Created for demonstration purposes only.

Vantic helps teams ship reliable AI applications. The platform is sold as three
products that share an account and a data model but are licensed, deployed, and
supported separately.

## 1. Vantic Evals

Offline evaluation. Golden datasets, rubric-driven scoring, LLM-as-judge,
regression detection, and CI gates that fail a build when scores drop against a
base branch.

Evals runs **cloud-only**. Judge models require Vantic-managed inference, so
there is no self-hosted deployment option for this product. Customers who cannot
send data to our cloud typically use Traces and Gateway only.

## 2. Vantic Traces

Production observability. Distributed tracing for LLM and agent runs, token and
cost attribution, latency breakdowns, online scoring of live traffic, and drift
alerting.

Traces is available cloud-hosted or **self-hosted** in the customer's own VPC.

## 3. Vantic Gateway

An inference proxy. Multi-provider routing, automatic failover, semantic
caching, rate limiting, and per-team spend controls. Applications call Gateway
instead of calling a model provider directly.

Gateway is available cloud-hosted or **self-hosted**, and is the only product
with an edge deployment option (§4).

## 4. Deployment matrix

| | Evals | Traces | Gateway |
|---|---|---|---|
| Cloud (multi-tenant) | ✓ | ✓ | ✓ |
| Self-hosted (customer VPC) | ✗ | ✓ | ✓ |
| Air-gapped | ✗ | ✓ | ✗ |
| Edge / regional PoP | ✗ | ✗ | ✓ |

Air-gapped Traces uses an offline license file. Gateway cannot run air-gapped
because it must reach upstream model providers by definition.

## 5. Buying together

The three products are commonly bought together but are not bundled
automatically. Cross-product discounts are negotiated on Enterprise. A customer
may hold different plan tiers on different products — for example Gateway on
Enterprise and Evals on Team.

Terminology note: "retention" means something different in each product. See
§3 of the security overview.
