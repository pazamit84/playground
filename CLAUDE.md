# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This is a "playground" repository with no application code yet. There is no `package.json`, build
system, linter or test suite, so there are no build, lint or test commands. The `.gitignore` is
the GitHub Node.js template.

## Delivery workflow

The repository uses the `delivery` plugin
([pazamit84/agent-delivery](https://github.com/pazamit84/agent-delivery)), enabled in
`.claude/settings.json`. Its skills form a pipeline, and each one reads the previous one's output
from `docs/features/<feature-slug>/`:

| Step | Command | Writes |
|------|---------|--------|
| 1 | `/delivery:product-manager <idea>` | `product.md` + `product-summary.md` |
| 2 | `/delivery:software-architect <slug>` | `architecture.md` + `architecture-summary.md` |
| 3 | `/delivery:tech-lead <slug>` | `plan.md` + `plan-summary.md` + `tasks/T-###-*.md` |
| 4 | `/delivery:developer [next \| T-### \| milestone M#]` | a branch and a PR |

`/delivery:board status` shows the task board, and `/delivery:board release <task-id> --feature <slug>`
releases a stale claim.

**Approval gates.** `product.md`, `architecture.md` and `plan.md` each carry `status:` in their
frontmatter. Agents always write `draft`. A document becomes `status: approved` either when the
user edits it themselves, or when Claude sets it after the user **explicitly** confirms in the
conversation that they reviewed and approve it. Each next skill refuses to run until the previous
document is approved, and tasks can't be claimed until `plan.md` is approved and merged into the
default branch. Never approve on your own initiative. Silence, "just continue" or "looks good, but…"
are not approval. Editing an approved document resets it to `draft` (bump `version`) so that it is
re-approved.

To change the pipeline itself, change the plugin repository, not this one.
