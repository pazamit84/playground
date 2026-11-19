---
feature: <feature-slug>
title: <Human-readable feature name>
status: draft
version: 1
updated: <YYYY-MM-DD>
---

# <Feature name>: Product Brief

> **Approval gate:** `status` stays `draft` until a human reviews this document and manually
> sets it to `approved`. `/software-architect` refuses to run until then. Any later change
> to this document resets `status` to `draft` and needs a new human approval.

## 1. Summary
<3–5 sentences: what we're building, for whom, and why now.>

## 2. Problem
- **Current situation:** <how things work today>
- **Who is affected:** <user segments and their volume>
- **Pain:** <what goes wrong, how often>
- **Evidence:** <data, tickets, user quotes, or "assumed, see A-n">
- **Cost of not solving:** <churn, revenue, support load, risk>

## 3. Goals and non-goals
**Goals**
- G-1: <outcome, not output>

**Non-goals**
- <explicitly out of scope, and why>

## 4. Users and personas
| Persona | Description | Primary need |
|---------|-------------|--------------|

## 5. User stories
| ID | As a… | I want… | So that… | Priority |
|----|-------|---------|----------|----------|
| US-1 | | | | Must |

## 6. Functional requirements
| ID | Requirement | Priority | Stories |
|----|-------------|----------|---------|
| FR-1 | The system shall … | Must | US-1 |

## 7. Non-functional requirements
| ID | Category | Requirement (measurable) |
|----|----------|--------------------------|
| NFR-1 | Performance | p95 … ≤ … ms at … requests/s |
| NFR-2 | Scale | Supports … records / … users now, … in 12 months |
| NFR-3 | Availability | … |
| NFR-4 | Security & privacy | … |
| NFR-5 | Accessibility | … |

## 8. User experience and flows
<Step-by-step main flow(s). For each screen or interaction, specify the default, loading, empty,
error and permission-denied states. Include a mermaid `journey` or `flowchart` if it adds clarity.
Link mockups if there are any.>

## 9. Acceptance criteria
| ID | Verifies | Given | When | Then |
|----|----------|-------|------|------|
| AC-1 | FR-1 | <precondition with concrete data> | <action> | <observable result> |

## 10. Success metrics
| ID | Metric | Baseline | Target | Measured by |
|----|--------|----------|--------|-------------|
| M-1 | | | | |

## 11. Scope and release
- **MVP (this release):** <FR ids>
- **Later:** <FR ids or ideas>
- **Rollout:** <feature flag, beta cohort, % rollout, migration of existing users/data>
- **Launch dependencies:** <docs, support training, comms>

## 12. Dependencies and constraints
- <other teams, services, vendors, legal, existing systems that must be reused>

## 13. Assumptions
- A-1: <assumption>, <impact if wrong>

## 14. Risks
| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R-1 | | | | |

## 15. Open questions
| ID | Question | Owner | Blocking? |
|----|----------|-------|-----------|
| Q-1 | | | yes/no |

## 16. Changelog
| Version | Date | Change |
|---------|------|--------|
| 1 | <YYYY-MM-DD> | Initial draft |
