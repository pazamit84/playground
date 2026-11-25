---
feature: <feature-slug>
source: plan.md
source_version: <version of plan.md this summarizes>
updated: <YYYY-MM-DD>
---

<!--
Summary rules (delete this comment in the output):
- A 2–3 minute read: 400–600 words, hard cap 700, tables included.
- Derived from plan.md and the task files only. Add nothing that isn't there. If they disagree, plan.md and the task files win.
- Cite milestone and task IDs (M#, T-###).
- Don't list every task. Show milestones, the critical path and anything unusual.
- No task status: status lives only in the task files and changes as work merges. Point readers to
  `taskboard.py status` for live progress.
- No `status` field: approval is given on plan.md, not on this file.
-->

# <Feature name>: Plan Summary

> A 2–3 minute summary of [plan.md](plan.md) (v<version>). The full plan and the task files are authoritative.

## The plan in one paragraph
<How the work is sliced, how many tasks, how much can run in parallel, and what ships first. 3–4 sentences.>

## Milestones
| Milestone | Delivers (what can be demoed) | Tasks | ACs passing at exit |
|-----------|-------------------------------|-------|---------------------|
| M1 | <one line> | <count> | <AC ids> |

## Critical path and parallelism
- **Critical path:** <T-001 → T-003 → …> (<length> tasks)
- **Maximum parallel tasks:** <n>, from <where>

## Things a reviewer should check
- <Risky tasks, contract-setting tasks, shared-file hotspots, flags, migrations>

## Decisions needed from you
- <Open question, with the default we'll use, and whether it blocks>

Live progress: `python3 .claude/skills/tech-lead/scripts/taskboard.py status --feature <feature-slug>`
