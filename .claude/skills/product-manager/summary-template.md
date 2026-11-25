---
feature: <feature-slug>
source: product.md
source_version: <version of product.md this summarizes>
updated: <YYYY-MM-DD>
---

<!--
Summary rules (delete this comment in the output):
- A 2–3 minute read: 400–600 words, hard cap 700, tables included.
- Derived from product.md only. Add nothing that isn't there. If the two disagree, product.md wins.
- Cite IDs (FR-n, AC-n, Q-n) so the reader can jump to the details in product.md.
- Bullets and short tables, no long prose. Leave out the full AC table and the changelog.
- No `status` field: approval is given on product.md, not on this file.
-->

# <Feature name>: Brief Summary

> A 2–3 minute summary of [product.md](product.md) (v<version>). The full brief is authoritative.

## In one paragraph
<What we're building, for whom, the problem it solves, and why now. 3–4 sentences.>

## Who it's for
- **<Persona>:** <primary need, one line>

## What's in the MVP
- <The capability in plain words> (FR-a, FR-b)

## What's deliberately out
- <Non-goal or later item, and why, in one line>

## Key numbers
| Target | Value |
|--------|-------|
| <Freshness / latency / scale / availability> | <number> (NFR-n) |

## Assumptions worth checking
- <The 3–5 assumptions that would change scope if wrong> (A-n)

## Decisions needed from you
- **Blocking:** <question> (Q-n)
- **Non-blocking:** <question, with the default we'll use> (Q-n)
