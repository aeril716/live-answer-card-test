# Vantic — Security Overview

> Fictional company. Created for demonstration purposes only.

Covers all three products unless a product is named specifically.

## 1. Certifications

### 1.1 SOC 2
Vantic holds **SOC 2 Type II** across all three products. The current report
covers a twelve-month observation window and was **renewed in March 2026**
following an external audit. We audit annually. The full report is available
under NDA through your account team.

Scope note: the SOC 2 report covers our cloud-hosted services. Self-hosted
deployments run in the customer's own environment and are outside the audit
boundary, though the same codebase is shipped.

### 1.2 ISO 27001
Certified for **Vantic Evals and Vantic Traces** since November 2024.
**Gateway is not currently in ISO scope** — it was added to the product line
after the certification audit and is expected to be included at the next
recertification in November 2026.

### 1.3 HIPAA
We do **not** sign Business Associate Agreements for any product. Customers
handling protected health information typically self-host Traces and Gateway and
keep PHI out of Evals entirely, since Evals has no self-hosted option (§1 of the
product overview).

### 1.4 GDPR
We act as processor. A DPA is available and standard contractual clauses are
in place for transfers out of the EEA. EU data residency is available for Traces
and Gateway; Evals processes in us-east-1 only.

### 1.5 Penetration testing
Third-party penetration tests run twice yearly across all products. An executive
summary of the most recent test is available under NDA. Remediation targets:
critical within 7 days, high within 30, medium within 90.

## 2. Training on customer data

**We never train models on customer data.** No customer prompt, completion,
trace, dataset, or cached response is used to train, fine-tune, or evaluate any
Vantic model or any third-party model. This commitment is contractual, not
policy, and applies identically across all three products.

Judge models used by Evals are third-party foundation models accessed under
zero-retention agreements with the providers.

## 3. Retention — differs by product

The word "retention" means something different in each product, and this is the
single most common source of confusion in security review.

| Product | What is retained | Default | Configurable range |
|---|---|---|---|
| Traces | Trace and span records | 90 days (Team) | 7–400 days |
| Gateway | Request logs | **7 days** | 1–30 days |
| Gateway | Semantic cache entries | 24 hours (TTL) | 1 hour – 7 days |
| Evals | Datasets and run history | **Indefinite** | Customer-deleted only |

Evals datasets are customer-owned artifacts and are never expired automatically;
deleting them is a customer action. Gateway request logs are deliberately short
because they sit on the hot inference path.

Deleted records are purged from backups within 35 days across all products.

## 4. Encryption

TLS 1.3 in transit, AES-256 at rest, all products. Customer-managed encryption
keys via AWS KMS are available on Enterprise for Traces and Evals.
**Gateway does not support customer-managed keys** in cloud mode; customers
requiring CMK for Gateway must self-host.

## 5. PII handling

Redaction of emails, phone numbers, payment card numbers, and national ID
formats is available, but implemented differently per product:

- **Traces** — redaction runs client-side inside the SDK, so unredacted values
  never reach Vantic infrastructure
- **Gateway** — redaction runs in the proxy, meaning the raw value does transit
  Gateway before being stripped from logs
- **Evals** — no automatic redaction. Datasets are assumed to be curated by the
  customer before upload

## 6. Access control

SAML 2.0 SSO and SCIM provisioning on Team and Enterprise, all products. RBAC
with four built-in roles; custom roles on Enterprise. Audit logs of all data
access are exportable via API and retained 400 days regardless of product-level
retention settings. Mandatory hardware-key MFA for all Vantic staff.

## 7. Regions

| Region | Evals | Traces | Gateway |
|---|---|---|---|
| us-east-1 | ✓ | ✓ | ✓ |
| eu-west-1 | ✗ | ✓ | ✓ |
| ap-southeast-2 | ✗ | ✓ | ✓ |

Region is selected at workspace creation and cannot be changed afterward.

## 8. Subprocessors and incidents

The current subprocessor list is published at vantic.example/subprocessors.
Enterprise customers receive 30 days notice before any addition. Confirmed
security incidents are disclosed to affected customers within **72 hours**.
Security contact: security@vantic.example.
