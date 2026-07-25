# Vantic — Integrations

> Fictional company. Created for demonstration purposes only.

## 1. SDKs

Official SDKs for **Python**, **TypeScript / JavaScript**, **Go**, and **Java**.

Coverage is not identical across products. The Go and Java SDKs support Traces
and Gateway but **not Evals** — the Evals API is available to those languages
over REST only. Python and TypeScript cover all three products.

## 2. Standards

**Traces** ingests OpenTelemetry natively and follows OpenInference semantic
conventions for LLM spans. A team already exporting OTel can point an existing
collector at our endpoint without code changes.

**Gateway** is not an OTel component. It emits its own request logs and can
forward them to Traces, but it is not a drop-in OTel collector.

**Evals** has no OTel surface.

## 3. Agent and application frameworks

Instrumentation for LangChain, LangGraph, LlamaIndex, CrewAI, Pydantic AI,
Haystack, DSPy, and the OpenAI Agents SDK. Framework instrumentation applies to
Traces. Gateway is framework-agnostic by design — it sits below the framework,
at the HTTP layer.

## 4. Model providers

Gateway routes to OpenAI, Anthropic, Google, Mistral, Cohere, Meta Llama via
Bedrock, Azure OpenAI, and any OpenAI-compatible endpoint including self-hosted
vLLM and Ollama.

Traces computes token counts and cost attribution for the same set. Cost
attribution for self-hosted models requires the customer to supply a cost-per-
token figure, since there is no provider invoice to reconcile against.

## 5. CI and source control

- GitHub Actions and GitLab CI: run an Evals suite as a pipeline step and fail
  the build on score regression
- GitHub pull request comments summarising score changes against the base branch
- Jenkins via the REST API
- CI integrations are an **Evals** feature. Traces and Gateway have no CI surface.

## 6. Alerting

Quality and drift alerts route to Slack, Microsoft Teams, PagerDuty, Opsgenie,
and generic webhooks. Alerting is available on Traces and Gateway. Evals reports
results into CI rather than into an alerting channel.

## 7. Data export

Trace and evaluation data can be exported to S3, BigQuery, and Snowflake on Team
and above. Scheduled warehouse sync to a customer-owned destination is
Enterprise-only.

Gateway request logs can be exported to S3 only, and only within their retention
window.

## 8. Not currently supported

No Zapier connector, no Datadog APM bridge, no native Salesforce integration, no
Terraform provider. These appear on the public roadmap without committed dates.

This list is not exhaustive. Absence of a tool from this document does not mean
it is unsupported — it means we have not documented a position on it. Ask your
account team.
