# Vantic Gateway — Technical Specification

> Fictional company. Created for demonstration purposes only.

## 1. What it is

An inference proxy. Applications send OpenAI-compatible requests to Gateway
instead of to a model provider. Gateway handles routing, failover, caching,
rate limiting, and spend control, then forwards upstream.

## 2. Added latency

These figures are **inference-path latency added by Gateway**, measured at the
proxy. They are unrelated to the support response times in the SLA.

| Path | p50 | p95 | p99 |
|---|---|---|---|
| Cache miss, same region | 4 ms | 11 ms | 24 ms |
| Cache miss, cross region | 38 ms | 71 ms | 110 ms |
| Cache hit | 9 ms | 18 ms | 31 ms |

A cache hit returns in single-digit to low-double-digit milliseconds against
hundreds or thousands of milliseconds for a live model call.

## 3. Semantic caching

Requests are embedded and matched against recent entries above a configurable
similarity threshold, default **0.95**. Default TTL is 24 hours, configurable
from 1 hour to 7 days.

Caching is **disabled by default** on new workspaces. It must be explicitly
enabled per route, because returning a cached completion is a product decision
rather than an infrastructure one.

Cache is scoped per workspace. Entries are never shared across customers.

## 4. Routing and failover

Routes are defined as an ordered list of targets with conditions. Failover
triggers on HTTP 429, HTTP 5xx, and timeout. Default retry policy is 2 attempts
with exponential backoff starting at 200 ms.

Weighted routing supports gradual rollout across model versions. Automatic
failover across providers requires the request to be provider-agnostic; requests
using provider-specific parameters fail over only within that provider.

## 5. Rate limiting and spend

Limits can be set per workspace, per team, per API key, and per route.
Enforcement is token-bucket with a 1-second window.

On reaching a spend cap, Gateway **alerts and continues serving**. It does not
block. See §4 of the pricing document.

## 6. Deployment

Cloud, self-hosted in customer VPC via Helm, or edge PoP for latency-sensitive
workloads. Edge is Enterprise-only and currently available in 6 metros.

**Air-gapped deployment is not possible** — Gateway must reach upstream model
providers over the network by definition.

## 7. Limits

- Maximum request body: 20 MB
- Maximum streaming response duration: 10 minutes
- Maximum configured routes per workspace: 200
- Concurrent connections per API key: 500 (Team), negotiated (Enterprise)
