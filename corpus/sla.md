# Vantic — Service Level Agreement

> Fictional company. Created for demonstration purposes only.

Applies to Enterprise customers. Starter and Team are provided without an
availability commitment on any product.

## 1. Availability — differs by product

| Product | Single region | Multi-region |
|---|---|---|
| Vantic Gateway | 99.95% | 99.99% |
| Vantic Traces | 99.9% | 99.95% |
| Vantic Evals | 99.5% | not offered |

Gateway carries the highest commitment because it sits on the customer's
inference path — an outage there takes the customer's application down, not just
their observability. Evals carries the lowest because it is a batch workload;
a delayed evaluation run is an inconvenience, not an outage.

Availability is measured per calendar month per product, excluding scheduled
maintenance under §4.

## 2. Service credits

| Monthly uptime against commitment | Credit |
|---|---|
| Missed by less than 1 point | 10% of that product's monthly fee |
| Missed by 1–5 points | 25% of that product's monthly fee |
| Missed by more than 5 points | 50% of that product's monthly fee |

Credits apply per product, not across the account — a Gateway outage does not
generate credits against a Traces subscription. Credits are requested within 30
days of the affected month and applied to the next invoice. Credits are the sole
remedy for availability shortfalls.

## 3. Support response times

These are **support ticket first-response times**. They are unrelated to the
inference latency figures in the Gateway specification, which are a different
measurement entirely.

| Severity | Definition | First response |
|---|---|---|
| S1 | Production inference or ingestion fully down | 1 hour, 24/7 |
| S2 | Major feature unusable, no workaround | 4 business hours |
| S3 | Degraded or partial impact | 1 business day |
| S4 | Question or feature request | 2 business days |

24/7 staffing applies to S1 only. S2 through S4 are covered 08:00–20:00 in the
customer's primary region, Monday through Friday, excluding local public
holidays.

Enterprise customers on Gateway may purchase an enhanced tier with a 15-minute
S1 first response. This is not available for Traces or Evals.

## 4. Maintenance

Scheduled maintenance occurs in a Sunday 02:00–06:00 window in the workspace's
region, announced at least 5 days in advance.

**Gateway is excluded from scheduled maintenance windows.** Gateway deploys are
rolling and zero-downtime by design; if a Gateway change requires downtime it is
treated as an incident, not maintenance.

Emergency maintenance may occur without notice and is excluded from availability
calculations only when it addresses an active security issue.

## 5. Data durability

Trace and dataset records are replicated across three availability zones.
Point-in-time recovery covering the preceding 7 days is available on Enterprise
for Traces and Evals. Gateway request logs are not covered by point-in-time
recovery given their 7-day retention.

## 6. Termination

On termination, customers may export all data via API or warehouse sync for
**60 days**, after which it is permanently deleted. This applies to Traces and
Evals. Gateway request logs follow their normal retention and are not extended
on termination.
