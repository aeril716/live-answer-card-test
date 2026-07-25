# Vantic — Pricing

> Fictional company. Created for demonstration purposes only.

Each product is priced independently. A customer may hold different tiers on
different products.

## 1. Vantic Traces

| | Starter | Team | Enterprise |
|---|---|---|---|
| Price | Free | $99 / month base | Custom, annual |
| Seats | 3 | 10, then $25 each | Unlimited |
| Included traces | 10,000 / month | 250,000 / month | Negotiated |
| Retention | 30 days | 90 days | 7–400 days |

Overage: **$0.40 per 1,000 traces** beyond the included volume.

## 2. Vantic Evals

| | Starter | Team | Enterprise |
|---|---|---|---|
| Price | Free | $149 / month base | Custom, annual |
| Seats | 2 | 10, then $25 each | Unlimited |
| Included eval runs | 500 / month | 50,000 / month | Negotiated |
| Datasets | 3 | Unlimited | Unlimited |

Overage: **$2.00 per 1,000 eval runs**. Runs using a large judge model count as
three runs against the allowance.

## 3. Vantic Gateway

Gateway is priced on request volume rather than seats.

| | Starter | Team | Enterprise |
|---|---|---|---|
| Price | Free | $0.50 per 10,000 requests | Custom, annual |
| Included requests | 50,000 / month | pay as you go | Committed volume |
| Cache hits | billed | **not billed** | not billed |
| Rate limit | 10 req/sec | 200 req/sec | Negotiated |

Cache hits are not billed on Team or Enterprise, so a well-tuned semantic cache
reduces the Gateway bill directly. **Model provider costs are separate** and are
billed by the provider to the customer; Vantic does not resell inference.

## 4. Spend controls

All products support a hard spend cap. Behaviour on reaching the cap differs:

- **Traces** — ingestion pauses; traces sent during the pause are dropped
- **Evals** — queued runs are held, not dropped, and resume next cycle
- **Gateway** — requests continue to be served and overage accrues, because
  cutting off inference would take the customer's application down

Gateway spend caps therefore alert rather than block. This is deliberate and is
the most common source of surprise on a first Gateway invoice.

## 5. Terms

- Monthly plans billed in advance, USD, by card
- Annual plans may be invoiced NET 30
- Annual prepay carries a 15% discount against monthly list
- Cross-product discounts negotiated on Enterprise
- Nonprofit and academic discounts available on request

## 6. Trials

Team is available on a 14-day trial with no card required, per product.
Enterprise trials run 30 days and include a guided onboarding session. Gateway
trials include 500,000 free requests rather than a time limit.
