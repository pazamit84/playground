# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This is a "playground" repository with no application code yet. There is no `package.json`, build
system, linter or test suite, so there are no build, lint or test commands. The `.gitignore` is
the GitHub Node.js template. What the repo does contain is a multi-agent delivery workflow,
implemented as project skills in `.claude/skills/`.

## Delivery workflow (skills)

The four skills form a pipeline. Each one reads the previous one's output from
`docs/features/<feature-slug>/`:

| Step | Skill | Reads | Writes |
|------|-------|-------|--------|
| 1 | `/product-manager <idea>` | the user's idea, the codebase | `product.md` (requirements with IDs FR-n, NFR-n, AC-n) |
| 2 | `/software-architect <slug>` | `product.md`, the codebase | `architecture.md` (design, contracts, mermaid diagrams) |
| 3 | `/tech-lead <slug>` | `architecture.md`, `product.md` | `plan.md` + `tasks/T-###-*.md` |
| 4 | `/developer [next \| T-### \| milestone M#]` | one task file | a branch and a PR |

**Human approval gates.** `product.md`, `architecture.md` and `plan.md` each carry `status:` in their
frontmatter. Agents always write `draft`. Only a human, editing the file by hand, sets
`status: approved`, and each next skill refuses to run until the previous document is approved:

- the architect and tech lead check with `taskboard.py gate <document> --feature <slug>`;
- the task board won't claim tasks unless `plan.md` is approved on the default branch;
- the PreToolUse hook `.claude/hooks/block-self-approval.py` (registered in `.claude/settings.json`)
  blocks any agent write that would leave a gated document approved. This also means editing an
  approved document requires resetting it to `draft`.

Never work around a closed gate, even when asked in chat.

The key design points:
- **Task files are self-contained.** A developer agent reads only its task file, not the
  architecture, so the tech lead copies the exact contracts into each task.
- **Task tracking is git-only**, implemented in `.claude/skills/tech-lead/scripts/taskboard.py`:
  - Status (`todo`/`done`) lives only in each task file's frontmatter on the default branch.
  - A task is claimed when the remote branch `task/<slug>/<task-id>` exists. Claims are created
    with an atomic, create-only push, so parallel agents can't take the same task.
  - The developer's PR sets `status: done`, so merging it unblocks the dependent tasks.
  - A milestone claim (`milestone/<slug>/M#`) claims all of its open tasks in one atomic push.
- **The plan must be merged** into the default branch before tasks can be claimed.
- **Developers follow** `.claude/skills/developer/references/coding-standards.md`: no
  duplication, small functions and descriptive names.

Common task board commands (run from the repo root):

```bash
python3 .claude/skills/tech-lead/scripts/taskboard.py status
```

```bash
python3 .claude/skills/tech-lead/scripts/taskboard.py validate --feature <slug>
```

```bash
python3 .claude/skills/tech-lead/scripts/taskboard.py claim --next
```

```bash
python3 .claude/skills/tech-lead/scripts/taskboard.py release --feature <slug> <task-id>
```

When changing `taskboard.py`, test it against a local bare repository (`git init --bare`) with two
clones acting as competing agents. Don't test against the real remote.
