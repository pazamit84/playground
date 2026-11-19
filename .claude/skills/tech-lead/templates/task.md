---
id: T-001
title: <Imperative, specific title, e.g. Add GET /orders endpoint with cursor pagination>
milestone: M1
status: todo
depends_on: []
size: S
---

# T-001: <title>

## Context
<2–4 sentences: why this task exists and where it fits in the feature. Enough for a developer
who has never seen the architecture. Optional background: [architecture §x](../architecture.md#…).>

## Objective
<One sentence describing the observable outcome when this task is done.>

## Scope
**In scope**
- <concrete item>

**Out of scope** (handled elsewhere: do not implement)
- <item> → T-00x

## Inputs from dependencies
<What already exists once the dependencies are merged: module paths, exported names, signatures.
Write "None" if there are no dependencies.>

## Implementation details
**Files**
| Action | Path | Notes |
|--------|------|-------|
| create | `src/…` | |
| modify | `src/…` | <what changes> |

**Follow the pattern in:** `<existing file that does something similar>`

**Contracts to implement** (copied verbatim from the architecture; do not change)
```<language>
<signatures / schemas / table DDL / error codes>
```

**Behavior and rules**
- <validation rule with concrete values>
- <edge case → expected handling>
- <error condition → error code / message>

## Provides
<Interfaces downstream tasks depend on. These are commitments: names, signatures, file paths.>

## Acceptance criteria
- [ ] <verifiable statement> (AC-n)
- [ ] <verifiable statement>

## Tests
| Type | Case | Input / setup | Expected |
|------|------|---------------|----------|
| unit | | | |
| integration | | | |

## Definition of done
- [ ] All acceptance criteria met and listed tests implemented
- [ ] Project test, lint, type-check and format commands pass
- [ ] Code follows `.claude/skills/developer/references/coding-standards.md`
- [ ] No changes outside the scope above
- [ ] `status: done` set in this file within the same PR
