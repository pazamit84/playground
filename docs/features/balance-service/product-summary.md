---
feature: balance-service
source: product.md
source_version: 1
updated: 2026-11-25
---

# Marketplace Balance Service: Brief Summary

> A 2–3 minute summary of [product.md](product.md) (v1). The full brief is authoritative.

## In one paragraph
Platforms are marketplaces whose vendors get paid by end clients, and each platform takes a fee
from every payment. Today nothing tracks who is owed what. Vendors can't see their earnings, and
platforms can't see what they owe or what they've earned. The balance service consumes payment,
refund and payout events, calculates each platform's fee, and keeps an auditable balance per vendor
and per platform in each currency. Admins read this through an API that existing portals display.

## Who it's for
- **Platform admin:** sees every vendor's balance and the fees collected, and sets the fee rule.
- **Vendor admin:** tracks their own balance and each payment, refund and payout.
- **Operator (internal):** fixes and reprocesses events that couldn't be applied.

## What's in the MVP
- Consumes **payment, refund and payout** events (FR-1–3).
- **Calculates the fee** from the platform's rule: a percentage plus an optional fixed amount per
  currency, capped at the gross amount and rounded half-up. Rule changes apply from a future time
  only (FR-4–6, FR-21).
- A payment credits the vendor with the **net** and the platform with the **fee**. A refund
  reverses both proportionally. A payout debits the vendor (FR-7, FR-8, FR-10).
- **A separate balance per currency**, never converted (FR-12).
- **Safe event handling:** each event counts once, a refund that arrives early waits up to 24 h,
  bad events go to a failed-events list operators can reprocess, and negative balances are flagged
  rather than rejected (FR-11, FR-13–16).
- **Read API:** vendor balances and filterable history (gross / fee / net), all of a platform's
  vendor balances, and fee reports per date range and per vendor (FR-18–20).
- **Strict tenant isolation:** each admin sees only their own vendor's or platform's data (NFR-7).

## What's deliberately out
- Moving money. Payouts are executed elsewhere; this service only records them.
- Currency conversion, chargebacks and disputes, holds and reserves (FR-23, FR-24).
- Its own UI. The portals consume the API.
- Tax, invoicing and accounting exports.
- **Next release:** per-vendor fee overrides (FR-22) and balances as of a past date (FR-25).

## Key numbers
| Target | Value |
|--------|-------|
| Event to visible balance | p95 ≤ 5 s (NFR-1) |
| Read API latency | p95 ≤ 300 ms at 200 req/s (NFR-2) |
| Volume now → 12 months | 1M → 5M events/day, peak 100 → 500/s (NFR-3) |
| Accuracy | 0 discrepancies in daily reconciliation (NFR-4) |
| Availability (read API) | 99.9% per month (NFR-6) |
| Record retention | 7 years (NFR-9) |

## Assumptions worth checking
- Refunds give back the fee proportionally (A-5).
- Payouts are decided upstream, so this service never blocks them (A-3).
- Each payment belongs to exactly one vendor, and each vendor to one platform (A-4, A-9).
- The volumes above are estimates (A-2).

## Decisions needed from you
- **Blocking (architecture):** which system publishes the events, through what channel and in
  what format, and are event IDs unique? (Q-1)
- **Blocking (architecture):** how are admins authenticated, and does an identity carry its
  platform and vendor? (Q-2)
- **Non-blocking:** backfill historical events at launch? (Q-3) Fee handling on refunds, defaulting
  to a proportional reversal (Q-4). Who edits fee rules, defaulting to platform admins (Q-5).
