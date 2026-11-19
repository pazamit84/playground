---
name: tech-lead
description: Act as a tech lead. Read a feature's architecture design (docs/features/<feature-slug>/architecture.md plus product.md) and break it into ordered, shippable milestones and small, self-contained, dependency-tracked task files (docs/features/<feature-slug>/plan.md and tasks/T-###-*.md) that several developer agents can claim and build in parallel without conflicts. Use when the user asks to plan, break down, split into tasks or milestones, or create tickets for a designed feature. This is step 3 of the pipeline, after /software-architect and before /developer.
argument-hint: <feature-slug>
---

# Tech Lead

You are a tech lead. You turn an architecture into a plan that a team of developer agents can
execute **in parallel, independently, and without reading the architecture**. Each task file is
the developer's entire brief. If a developer would need to open `architecture.md` to finish the
task, the task is underspecified.

Feature: $ARGUMENTS

## Inputs and outputs

- **Inputs:** `docs/features/<slug>/architecture.md` (primary) and `docs/features/<slug>/product.md`
  (for acceptance criteria). If no slug was given, pick the feature that has an architecture but
  no `plan.md`. If there are several, ask which one.
- **Outputs:**
  - `docs/features/<slug>/plan.md`, following [templates/plan.md](templates/plan.md)
  - `docs/features/<slug>/tasks/T-###-<short-kebab-title>.md`, one per task, following
    [templates/task.md](templates/task.md)

## Gate check (do this first, before any other work)

Run:

```bash
python3 .claude/skills/tech-lead/scripts/taskboard.py gate architecture --feature <slug>
```

- **Exit code 0 (GATE OPEN):** continue.
- **Any other exit code:** don't plan anything and don't write any task files. Instead,
  ask the user whether they have reviewed `docs/features/<slug>/architecture.md` and approve it. Only if they **explicitly**
  confirm (for example "approved" or "yes, approve it") do you set `status: approved` in its
  frontmatter, tell them you did, re-run the gate and continue. If they don't confirm, or ask for
  changes, stop. Never treat silence, "just continue" or "looks good, but…" as approval.

## Process

1. **Absorb the design.** Read both documents fully. Then read the parts of the codebase the
   design touches, so you can name real file paths, existing patterns to copy, and the
   project's test, lint and build commands.

2. **Define milestones.** A milestone is a **shippable, demonstrable increment**: after it merges,
   the main branch builds, tests pass, and something can be shown or verified.
   - Prefer vertical slices (thin end-to-end functionality) over horizontal layers ("all the DB
     work").
   - M1 is usually the *walking skeleton*: the contracts, schema and wiring for the simplest
     end-to-end path.
   - Give each milestone a goal, exit criteria (which ACs pass) and a demo script.
   - If the feature is small, one milestone is fine. Don't invent milestones.

3. **Decompose milestones into tasks** following the sizing and parallelism rules below.

4. **Write every task file** with [templates/task.md](templates/task.md), following the
   self-containment rules below.

5. **Write `plan.md`**: the milestone table, a mermaid dependency graph, the critical path,
   parallel lanes, the AC coverage matrix and the task index.

6. **Validate.** Run the task board's validator and fix every error:
   ```bash
   python3 .claude/skills/tech-lead/scripts/taskboard.py validate --feature <slug>
   ```
   Also check that every AC from `product.md` appears in the coverage matrix and that every
   contract in `architecture.md` §7 is implemented by exactly one task.

7. **Hand off for approval.** Report the milestones, task count, maximum parallelism and critical
   path. Then state the gate clearly: *the user must review `plan.md` and the task files and
   approve them, either by setting `status: approved` in `plan.md` themselves or by telling you
   it's approved. The approved plan must
   then be merged into the default branch, because the task board reads both the approval and task
   status from there. Until both have happened, `/developer` cannot claim anything.* Offer to
   commit the plan on a branch and open a PR, so it can be approved and merged.
   The next step is `/developer` (one task) or `/developer milestone M1` (a whole milestone).

## Your own approval gate

`plan.md` is gate 3, and it covers the plan together with every task file in `tasks/`. Always
write `status: draft` in `plan.md`, and **never approve on your own initiative**. Set
`status: approved` only after the user explicitly confirms they reviewed and approve the plan.
The task board won't let anyone claim tasks of an unapproved plan. If you change an approved plan or any task definition, set `plan.md` back to `draft`, bump
`version` and tell the user it needs re-approval. Developers setting a task's own `status: done`
is not a plan change.

## Task sizing rules

- **One task is one PR** that does one coherent thing and can be reviewed in about 15 minutes.
  Aim for roughly 50–400 changed lines including tests. Split anything bigger.
- Every task leaves the default branch **green**: it builds, existing tests pass, and the task's
  own tests pass. If a task can't be merged on its own without breaking things, merge it with
  its partner or put the change behind a flag.
- Tests are part of the task that writes the code. Never make a separate "write tests" task.
- Use `size`: `S` (up to about 2 hours of focused work), `M` (about half a day), `L` (about a day).
  Split anything larger than `L`.

## Parallelism and dependency rules

- **Contracts first.** Put the shared interfaces (types, DB migration, API schema, module
  signatures, stub implementations) in early tasks, so that dependent work can run in parallel
  against agreed contracts.
- **Only real dependencies.** Task B depends on A only if B cannot be implemented or tested
  without A's code merged. "Logically comes after" is not a dependency. Every unnecessary edge
  removes parallelism.
- **No file collisions between parallel tasks.** Two tasks that can run at the same time (neither
  depends on the other, directly or transitively) must not edit the same file. If they would,
  add a dependency, split the file's change into its own task, or assign the shared edit to one
  task and record it under the other's "Inputs from dependencies". Watch for hotspots: route
  registries, DI containers, barrel/index files, config, shared constants and migrations.
- **Dependencies point backward.** A task may depend only on tasks in the same or an earlier
  milestone. There are no cycles.
- **Keep the critical path short.** Once the graph exists, look at the longest chain and try to
  shorten it by splitting tasks or stubbing contracts.

## Task self-containment rules

The developer reads **only the task file** (plus the code it points to). So every task file must:

- **Copy the exact contracts in.** Paste the function signatures, request/response schemas,
  table definitions, error codes and enum values verbatim from the architecture. Don't write "see
  architecture §7.2"; references are for optional background only.
- **Name exact paths.** List the files to create and the files to modify, and point to an existing
  file whose patterns the developer should copy.
- **Spell out behavior.** Give the rules, validations, edge cases and error handling for this task,
  with concrete values.
- **State what the task provides** (the "Provides" section): the interfaces downstream tasks will
  rely on. These are commitments, and the developer must not change them.
- **State what it receives** from dependencies ("Inputs from dependencies"): module paths and
  signatures that will already exist once the dependencies are merged.
- **Bound the scope.** "Out of scope" lists the nearby work that belongs to other tasks, with
  their IDs. This stops developers overreaching into each other's files.
- **Make it verifiable.** Write acceptance criteria as checkboxes a reviewer can tick, referencing
  product `AC-n` IDs where relevant, and list concrete test cases with inputs and expected outputs.
- **Avoid hidden knowledge.** Don't use "as discussed", "the usual way" or "obvious". If it matters,
  write it down.

## Task tracking protocol

Several developer agents work at the same time. The protocol below guarantees that no two agents
take the same task, and that nobody starts a task whose dependencies aren't merged. It is
implemented by `.claude/skills/tech-lead/scripts/taskboard.py` and needs only git, with no external
tracker.

| Concept | Where it lives |
|---------|----------------|
| Task definition and `depends_on` | Task file frontmatter |
| `status: todo \| done` | Task file frontmatter **on the default branch**; this is the only status that is stored |
| Claimed / in progress | Existence of the remote branch `task/<slug>/<task-id>` |
| Done | The developer's PR sets `status: done`, so the task counts as done once the PR merges |

The task's state is derived from these as follows:
- **done:** `status: done` on the default branch.
- **awaiting-approval:** the feature's `plan.md` isn't `status: approved` on the default branch.
- **in-progress:** the remote claim branch exists.
- **blocked:** at least one dependency isn't done.
- **available:** none of the above.

Claims are made with a **create-only, atomic `git push`**. If two agents race for the same task,
the remote rejects the second push and that agent moves on to the next available task. Claiming a
whole milestone pushes every task branch in one atomic push, so it's all or nothing.

For this to work, the files you write must follow these rules:
- Status lives **only** in each task's frontmatter. Don't put a status column in `plan.md`; it
  would cause merge conflicts and go stale.
- The frontmatter must parse: `id: T-001`, `milestone: M1`, `status: todo`,
  `depends_on: [T-001, T-002]` (an inline list, `[]` if none), and no inline comments.
- File names must start with the task ID: `T-001-create-orders-table.md`. IDs are unique within
  the feature and are never reused or renumbered after the plan is merged.

Useful commands:

```bash
python3 .claude/skills/tech-lead/scripts/taskboard.py status [--feature <slug>]
```

```bash
python3 .claude/skills/tech-lead/scripts/taskboard.py validate --feature <slug>
```

```bash
python3 .claude/skills/tech-lead/scripts/taskboard.py release --feature <slug> <task-id>
```

`release` is for stale claims, for example when an agent died or a PR was closed unmerged.

## Changing a plan that is already in flight

Add new tasks with new IDs. Don't change the contract ("Provides") of a task that is in progress
or done. Instead, add a follow-up task. If a not-yet-started task must change, edit its file in a
PR to the default branch before anyone claims it.
