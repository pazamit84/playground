---
feature: <feature-slug>
source: architecture.md
source_version: <version of architecture.md this summarizes>
updated: <YYYY-MM-DD>
---

<!--
Summary rules (delete this comment in the output):
- A 2–3 minute read: 400–600 words, hard cap 700, tables and the diagram included.
- Derived from architecture.md only. Add nothing that isn't there. If the two disagree, architecture.md wins.
- Cite section numbers and IDs (FR-n, NFR-n) so the reader can jump to the details.
- At most one diagram: the component diagram from architecture.md, at 10 nodes or fewer.
- Leave out full schemas, endpoint payloads and the traceability table.
- No `status` field: approval is given on architecture.md, not on this file.
-->

# <Feature name>: Architecture Summary

> A 2–3 minute summary of [architecture.md](architecture.md) (v<version>). The full design is authoritative.

## The design in one paragraph
<The shape of the solution and why it's the simplest design that meets the brief. 3–4 sentences.>

## Components
<Optional mermaid flowchart, 10 nodes or fewer, with a one-line caption.>

| Component | Responsibility |
|-----------|----------------|
| <name> | <one line> |

## Key decisions
- **<Decision>:** <what was chosen, the main alternative rejected, and why> (§n)

## How it meets the hard requirements
| Requirement | How |
|-------------|-----|
| <NFR-n: the target> | <one line> |

## Top risks and failure modes
- <Risk, and its mitigation, in one line>

## Decisions needed from you
- <Open question, with the default we'll use, and whether it blocks>
