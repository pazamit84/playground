#!/usr/bin/env python3
"""Task board for the product-manager -> architect -> tech-lead -> developer workflow.

Source of truth (no external tracker needed):
  * A task's `status` (todo | done) lives in the frontmatter of
    docs/features/<feature>/tasks/<task-id>-<slug>.md on the base branch.
  * A task is CLAIMED when the remote branch task/<feature>/<task-id> exists.
    Claims are created with a create-only, atomic push, so two agents can never
    claim the same task: the second push is rejected by the remote.
  * A developer's PR flips the task's status to `done`; merging that PR marks the
    task done on the base branch and unblocks its dependents.

Derived state of each task:
  done        status is `done` on the base branch
  in-progress claim branch exists on the remote
  blocked     at least one dependency is not done
  awaiting-approval  the feature's plan.md is not `status: approved` on the base branch
                     (approval gate: nothing can be claimed until the user approves the plan)
  available   none of the above -> can be claimed

Approval gates: product.md, architecture.md and plan.md carry `status:` in their frontmatter.
It is set to `approved` only with the user's explicit approval; `gate` checks it for the skills.

Run `taskboard.py --help` for commands.
"""
from __future__ import annotations

import argparse
import os
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

FEATURES_ROOT = "docs/features"
TASK_BRANCH_PREFIX = "task"
MILESTONE_BRANCH_PREFIX = "milestone"
TASK_FILE_PATTERN = re.compile(r"^docs/features/(?P<feature>[^/]+)/tasks/(?P<name>[^/]+)\.md$")
TASK_ID_PATTERN = re.compile(r"^T-\d+$")
MILESTONE_ID_PATTERN = re.compile(r"^M\d+$")
STATUS_LINE_PATTERN = re.compile(r"^status:.*$", re.MULTILINE)
REQUIRED_FIELDS = ("id", "title", "milestone", "status", "depends_on")
VALID_STATUSES = ("todo", "done")

APPROVED_STATUS = "approved"
GATED_DOCUMENTS = ("product", "architecture", "plan")

STATE_DONE = "done"
STATE_IN_PROGRESS = "in-progress"
STATE_BLOCKED = "blocked"
STATE_AVAILABLE = "available"
STATE_AWAITING_APPROVAL = "awaiting-approval"

EXIT_NOTHING_AVAILABLE = 3
EXIT_CLAIM_LOST = 4
EXIT_GATE_CLOSED = 5
MAX_CLAIM_ATTEMPTS = 5


class BoardError(Exception):
    """A user-facing error that aborts the command."""


@dataclass(frozen=True)
class Task:
    feature: str
    task_id: str
    title: str
    milestone: str
    status: str
    depends_on: tuple[str, ...]
    path: str

    @property
    def claim_branch(self) -> str:
        return f"{TASK_BRANCH_PREFIX}/{self.feature}/{self.task_id}"

    @property
    def sort_key(self) -> tuple:
        return (self.feature, numeric_suffix(self.milestone), numeric_suffix(self.task_id))


# --------------------------------------------------------------------------- git helpers


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise BoardError(f"`git {' '.join(args)}` failed:\n{result.stderr.strip()}")
    return result


def detect_base_branch() -> str:
    symbolic = run_git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False)
    if symbolic.returncode == 0:
        return symbolic.stdout.strip().removeprefix("origin/")
    for candidate in ("main", "master"):
        if run_git("ls-remote", "--exit-code", "--heads", "origin", candidate, check=False).returncode == 0:
            return candidate
    raise BoardError("Could not detect the default branch; pass --base <branch>.")


def fetch_base(base_branch: str) -> str:
    """Fetch the base branch and return the ref to read task files from."""
    remote_ref = f"refs/remotes/origin/{base_branch}"
    run_git("fetch", "--quiet", "origin", f"+refs/heads/{base_branch}:{remote_ref}")
    return remote_ref


def list_remote_branches() -> set[str]:
    output = run_git("ls-remote", "--heads", "origin").stdout
    return {
        line.split("\t", 1)[1].removeprefix("refs/heads/")
        for line in output.splitlines()
        if "\t" in line
    }


def repo_root() -> Path:
    return Path(run_git("rev-parse", "--show-toplevel").stdout.strip())


def ensure_clean_worktree() -> None:
    if run_git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        raise BoardError("Working tree has uncommitted changes; commit or stash them first.")


def create_claim_commit(base_ref: str, agent: str, subject: str) -> str:
    """Create an empty commit on top of base_ref. Its unique message makes its SHA unique,
    so a competing claim can never be a fast-forward of ours."""
    tree = run_git("rev-parse", f"{base_ref}^{{tree}}").stdout.strip()
    parent = run_git("rev-parse", base_ref).stdout.strip()
    message = f"{subject}\n\nClaimed-By: {agent}\nClaimed-At-Ns: {time.time_ns()}"
    return run_git("commit-tree", tree, "-p", parent, "-m", message).stdout.strip()


def push_new_branches_atomically(commit: str, branches: list[str]) -> bool:
    """Create all branches at `commit` or none of them. Fails if any branch already exists."""
    leases = [f"--force-with-lease=refs/heads/{branch}:" for branch in branches]
    refspecs = [f"{commit}:refs/heads/{branch}" for branch in branches]
    result = run_git("push", "--atomic", "--quiet", "origin", *leases, *refspecs, check=False)
    return result.returncode == 0


# --------------------------------------------------------------------------- task parsing


def numeric_suffix(identifier: str) -> int:
    digits = re.findall(r"\d+", identifier)
    return int(digits[-1]) if digits else 0


def parse_frontmatter(text: str, path: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise BoardError(f"{path}: missing frontmatter (file must start with '---').")
    fields: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        key, separator, raw_value = line.partition(":")
        if separator and key.strip():
            fields[key.strip()] = parse_frontmatter_value(raw_value.strip())
    raise BoardError(f"{path}: frontmatter is not closed with '---'.")


def parse_frontmatter_value(raw_value: str) -> str | list[str]:
    if raw_value.startswith("[") and raw_value.endswith("]"):
        return [item.strip().strip("'\"") for item in raw_value[1:-1].split(",") if item.strip()]
    return raw_value.strip("'\"")


def document_status(text: str, path: str) -> str:
    """Return the lower-cased `status` of a gated document, ignoring any inline comment."""
    status = parse_frontmatter(text, path).get("status", "")
    return str(status).split("#", 1)[0].strip().lower()


def feature_document_path(feature: str, document: str) -> str:
    return f"{FEATURES_ROOT}/{feature}/{document}.md"


def build_task(feature: str, path: str, text: str) -> Task:
    fields = parse_frontmatter(text, path)
    missing = [name for name in REQUIRED_FIELDS if name not in fields]
    if missing:
        raise BoardError(f"{path}: missing frontmatter fields: {', '.join(missing)}")
    dependencies = fields["depends_on"]
    if isinstance(dependencies, str):
        raise BoardError(f"{path}: depends_on must be an inline list, e.g. [T-001, T-002] or [].")
    return Task(
        feature=feature,
        task_id=fields["id"],
        title=fields["title"],
        milestone=fields["milestone"],
        status=fields["status"],
        depends_on=tuple(dependencies),
        path=path,
    )


def load_tasks_from_ref(ref: str, feature: str | None) -> list[Task]:
    listing = run_git("ls-tree", "-r", "--name-only", ref, "--", FEATURES_ROOT, check=False).stdout
    return [
        build_task(match["feature"], path, run_git("show", f"{ref}:{path}").stdout)
        for path in listing.splitlines()
        if (match := TASK_FILE_PATTERN.match(path)) and feature in (None, match["feature"])
    ]


def load_approved_features_from_ref(ref: str, features: set[str]) -> set[str]:
    approved = set()
    for feature in features:
        plan_path = feature_document_path(feature, "plan")
        plan = run_git("show", f"{ref}:{plan_path}", check=False)
        if plan.returncode == 0 and document_status(plan.stdout, plan_path) == APPROVED_STATUS:
            approved.add(feature)
    return approved


def load_tasks_from_worktree(feature: str | None) -> list[Task]:
    root = repo_root()
    tasks = []
    for file_path in sorted((root / FEATURES_ROOT).glob("*/tasks/*.md")):
        relative_path = file_path.relative_to(root).as_posix()
        match = TASK_FILE_PATTERN.match(relative_path)
        if match and feature in (None, match["feature"]):
            tasks.append(build_task(match["feature"], relative_path, file_path.read_text()))
    return tasks


# --------------------------------------------------------------------------- board state


class Board:
    def __init__(self, tasks: list[Task], remote_branches: set[str], approved_features: set[str]):
        self.tasks = sorted(tasks, key=lambda task: task.sort_key)
        self.remote_branches = remote_branches
        self.approved_features = approved_features
        self._by_key = {(task.feature, task.task_id): task for task in self.tasks}

    def find(self, feature: str, task_id: str) -> Task:
        task = self._by_key.get((feature, task_id))
        if task is None:
            raise BoardError(f"Task {task_id} not found in feature '{feature}' on the base branch.")
        return task

    def is_done(self, feature: str, task_id: str) -> bool:
        task = self._by_key.get((feature, task_id))
        return task is not None and task.status == STATE_DONE

    def unmet_dependencies(self, task: Task) -> list[str]:
        return [dep for dep in task.depends_on if not self.is_done(task.feature, dep)]

    def state_of(self, task: Task) -> str:
        if task.status == STATE_DONE:
            return STATE_DONE
        if task.feature not in self.approved_features:
            return STATE_AWAITING_APPROVAL
        if task.claim_branch in self.remote_branches:
            return STATE_IN_PROGRESS
        if self.unmet_dependencies(task):
            return STATE_BLOCKED
        return STATE_AVAILABLE

    def available_tasks(self, feature: str | None, milestone: str | None) -> list[Task]:
        return [
            task
            for task in self.tasks
            if self.state_of(task) == STATE_AVAILABLE
            and feature in (None, task.feature)
            and milestone in (None, task.milestone)
        ]

    def milestone_tasks(self, feature: str, milestone: str) -> list[Task]:
        tasks = [task for task in self.tasks if task.feature == feature and task.milestone == milestone]
        if not tasks:
            raise BoardError(f"No tasks found for milestone {milestone} in feature '{feature}'.")
        return tasks


def load_board(args: argparse.Namespace) -> tuple[Board, str]:
    base_branch = args.base or detect_base_branch()
    base_ref = fetch_base(base_branch)
    tasks = load_tasks_from_ref(base_ref, args.feature)
    approved_features = load_approved_features_from_ref(base_ref, {task.feature for task in tasks})
    return Board(tasks, list_remote_branches(), approved_features), base_ref


def topological_order(tasks: list[Task]) -> list[Task]:
    """Order tasks so every task comes after its dependencies within the given set."""
    remaining = {task.task_id: task for task in tasks}
    ordered: list[Task] = []
    while remaining:
        ready = [
            task for task in remaining.values()
            if not any(dep in remaining for dep in task.depends_on)
        ]
        if not ready:
            raise BoardError(f"Dependency cycle among: {', '.join(sorted(remaining))}")
        for task in sorted(ready, key=lambda task: task.sort_key):
            ordered.append(task)
            del remaining[task.task_id]
    return ordered


def agent_name(args: argparse.Namespace) -> str:
    return args.agent or os.environ.get("TASKBOARD_AGENT") or f"{socket.gethostname()}-{os.getpid()}"


# --------------------------------------------------------------------------- commands


def command_status(args: argparse.Namespace) -> int:
    board, _ = load_board(args)
    if not board.tasks:
        print("No tasks found on the base branch. Has the tech-lead plan been merged?")
        return 0
    counts: dict[str, int] = {}
    print(f"{'STATE':<18} {'FEATURE':<24} {'ID':<7} {'MS':<4} {'DEPENDS ON':<18} TITLE")
    for task in board.tasks:
        state = board.state_of(task)
        counts[state] = counts.get(state, 0) + 1
        dependencies = ",".join(task.depends_on) or "-"
        print(f"{state:<18} {task.feature:<24} {task.task_id:<7} {task.milestone:<4} {dependencies:<18} {task.title}")
    print("\n" + "  ".join(f"{state}: {count}" for state, count in sorted(counts.items())))
    return 0


def command_next(args: argparse.Namespace) -> int:
    board, _ = load_board(args)
    candidates = board.available_tasks(args.feature, args.milestone)
    if not candidates:
        print("No available task (all remaining tasks are blocked, in progress or done).")
        return EXIT_NOTHING_AVAILABLE
    print_task_location(candidates[0])
    return 0


def print_task_location(task: Task) -> None:
    print(f"FEATURE={task.feature}\nTASK={task.task_id}\nMILESTONE={task.milestone}\n"
          f"FILE={task.path}\nBRANCH={task.claim_branch}")


def command_claim(args: argparse.Namespace) -> int:
    ensure_clean_worktree()
    if not args.next and not (args.feature and args.task_id):
        raise BoardError("Use `claim --next [--feature F] [--milestone M]` or `claim --feature F <task-id>`.")
    attempts = MAX_CLAIM_ATTEMPTS if args.next else 1
    for _ in range(attempts):
        board, base_ref = load_board(args)
        task = pick_task_to_claim(board, args)
        if task is None:
            print("No available task to claim.")
            return EXIT_NOTHING_AVAILABLE
        if try_claim_task(task, base_ref, agent_name(args)):
            print(f"Claimed {task.task_id}; checked out {task.claim_branch}.")
            print_task_location(task)
            return 0
        print(f"Lost the race for {task.task_id} (claimed by another agent).", file=sys.stderr)
    return EXIT_CLAIM_LOST


def pick_task_to_claim(board: Board, args: argparse.Namespace) -> Task | None:
    if args.next:
        candidates = board.available_tasks(args.feature, args.milestone)
        return candidates[0] if candidates else None
    task = board.find(args.feature, args.task_id)
    state = board.state_of(task)
    if state == STATE_AWAITING_APPROVAL:
        raise BoardError(f"Gate closed: {feature_document_path(task.feature, 'plan')} is not approved "
                         "on the base branch. The user must approve it and merge it.")
    if state != STATE_AVAILABLE:
        detail = f" (waiting on {', '.join(board.unmet_dependencies(task))})" if state == STATE_BLOCKED else ""
        raise BoardError(f"{task.task_id} is {state}{detail}; it cannot be claimed.")
    return task


def try_claim_task(task: Task, base_ref: str, agent: str) -> bool:
    commit = create_claim_commit(base_ref, agent, f"claim: {task.feature} {task.task_id}")
    if not push_new_branches_atomically(commit, [task.claim_branch]):
        return False
    run_git("checkout", "--quiet", "-B", task.claim_branch, commit)
    return True


def command_claim_milestone(args: argparse.Namespace) -> int:
    ensure_clean_worktree()
    board, base_ref = load_board(args)
    open_tasks = [task for task in board.milestone_tasks(args.feature, args.milestone) if task.status != STATE_DONE]
    if not open_tasks:
        print(f"Milestone {args.milestone} is already done.")
        return EXIT_NOTHING_AVAILABLE
    ensure_milestone_claimable(board, open_tasks)
    milestone_branch = f"{MILESTONE_BRANCH_PREFIX}/{args.feature}/{args.milestone}"
    branches = [milestone_branch, *(task.claim_branch for task in open_tasks)]
    commit = create_claim_commit(base_ref, agent_name(args), f"claim: {args.feature} {args.milestone}")
    if not push_new_branches_atomically(commit, branches):
        print("Lost the race: another agent claimed part of this milestone.", file=sys.stderr)
        return EXIT_CLAIM_LOST
    run_git("checkout", "--quiet", "-B", milestone_branch, commit)
    print(f"Claimed {len(open_tasks)} task(s); checked out {milestone_branch}.")
    print("Execution order:")
    for task in topological_order(open_tasks):
        print(f"  {task.task_id}  {task.path}  {task.title}")
    return 0


def ensure_milestone_claimable(board: Board, open_tasks: list[Task]) -> None:
    open_ids = {task.task_id for task in open_tasks}
    for task in open_tasks:
        if board.state_of(task) == STATE_AWAITING_APPROVAL:
            raise BoardError(f"Gate closed: {feature_document_path(task.feature, 'plan')} is not approved "
                             "on the base branch. The user must approve it and merge it.")
        if board.state_of(task) == STATE_IN_PROGRESS:
            raise BoardError(f"{task.task_id} is already claimed by another agent; cannot claim the whole milestone.")
        external_blockers = [dep for dep in board.unmet_dependencies(task) if dep not in open_ids]
        if external_blockers:
            raise BoardError(f"{task.task_id} depends on unfinished task(s) outside the milestone: "
                             f"{', '.join(external_blockers)}")
    topological_order(open_tasks)


def command_release(args: argparse.Namespace) -> int:
    branch = f"{TASK_BRANCH_PREFIX}/{args.feature}/{args.task_id}"
    if branch not in list_remote_branches():
        print(f"{branch} is not claimed.")
        return 0
    base_ref = fetch_base(args.base or detect_base_branch())
    run_git("fetch", "--quiet", "origin", f"refs/heads/{branch}")
    commits_beyond_base = int(run_git("rev-list", "--count", f"{base_ref}..FETCH_HEAD").stdout.strip())
    if commits_beyond_base > 1 and not args.force:
        raise BoardError(f"{branch} contains work beyond the claim commit; re-run with --force to discard it.")
    run_git("push", "--quiet", "origin", "--delete", branch)
    print(f"Released {args.task_id} ({branch} deleted).")
    return 0


def command_mark_done(args: argparse.Namespace) -> int:
    task = next((t for t in load_tasks_from_worktree(args.feature) if t.task_id == args.task_id), None)
    if task is None:
        raise BoardError(f"Task {args.task_id} not found in docs/features/{args.feature}/tasks/.")
    task_file = repo_root() / task.path
    task_file.write_text(STATUS_LINE_PATTERN.sub(f"status: {STATE_DONE}", task_file.read_text(), count=1))
    print(f"Marked {task.task_id} as done in {task.path}. Commit this change in your PR.")
    return 0


def command_gate(args: argparse.Namespace) -> int:
    """Exit 0 only if the given document is approved (read from the working tree)."""
    relative_path = feature_document_path(args.feature, args.document)
    document_file = repo_root() / relative_path
    if not document_file.exists():
        print(f"GATE CLOSED: {relative_path} does not exist.")
        return EXIT_GATE_CLOSED
    status = document_status(document_file.read_text(), relative_path)
    if status != APPROVED_STATUS:
        print(f"GATE CLOSED: {relative_path} has status '{status or 'missing'}'. "
              f"The user must review and approve it (`status: {APPROVED_STATUS}`) before the next step can run.")
        return EXIT_GATE_CLOSED
    print(f"GATE OPEN: {relative_path} is approved.")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    tasks = load_tasks_from_worktree(args.feature)
    if not tasks:
        raise BoardError("No task files found under docs/features/*/tasks/.")
    errors = collect_validation_errors(tasks)
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Validated {len(tasks)} task(s): {'FAILED' if errors else 'OK'}.")
    return 1 if errors else 0


def collect_validation_errors(tasks: list[Task]) -> list[str]:
    errors: list[str] = []
    for feature in sorted({task.feature for task in tasks}):
        feature_tasks = [task for task in tasks if task.feature == feature]
        errors.extend(validate_feature(feature, feature_tasks))
    return errors


def validate_feature(feature: str, tasks: list[Task]) -> list[str]:
    errors: list[str] = []
    if not (repo_root() / FEATURES_ROOT / feature / "plan.md").exists():
        errors.append(f"{feature}: plan.md is missing.")
    by_id: dict[str, Task] = {}
    for task in tasks:
        errors.extend(validate_task_fields(task))
        if task.task_id in by_id:
            errors.append(f"{task.path}: duplicate id {task.task_id} (also in {by_id[task.task_id].path}).")
        by_id[task.task_id] = task
    for task in tasks:
        errors.extend(validate_task_dependencies(task, by_id))
    try:
        topological_order(tasks)
    except BoardError as cycle_error:
        errors.append(f"{feature}: {cycle_error}")
    return errors


def validate_task_fields(task: Task) -> list[str]:
    errors = []
    if not TASK_ID_PATTERN.match(task.task_id):
        errors.append(f"{task.path}: id '{task.task_id}' must look like T-001.")
    if not Path(task.path).name.startswith(f"{task.task_id}-"):
        errors.append(f"{task.path}: file name must start with '{task.task_id}-'.")
    if not MILESTONE_ID_PATTERN.match(task.milestone):
        errors.append(f"{task.path}: milestone '{task.milestone}' must look like M1.")
    if task.status not in VALID_STATUSES:
        errors.append(f"{task.path}: status '{task.status}' must be one of {', '.join(VALID_STATUSES)}.")
    return errors


def validate_task_dependencies(task: Task, by_id: dict[str, Task]) -> list[str]:
    errors = []
    for dependency_id in task.depends_on:
        dependency = by_id.get(dependency_id)
        if dependency_id == task.task_id:
            errors.append(f"{task.path}: task depends on itself.")
        elif dependency is None:
            errors.append(f"{task.path}: unknown dependency {dependency_id}.")
        elif numeric_suffix(dependency.milestone) > numeric_suffix(task.milestone):
            errors.append(f"{task.path}: depends on {dependency_id} from a later milestone ({dependency.milestone}).")
    return errors


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", help="Base branch holding the plan (default: the remote's default branch).")
    parser.add_argument("--agent", help="Agent name recorded in claims (default: $TASKBOARD_AGENT or host-pid).")
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser("status", help="Show every task and its derived state.")
    status.add_argument("--feature")
    status.set_defaults(handler=command_status)

    next_task = commands.add_parser("next", help="Print the next available task without claiming it.")
    next_task.add_argument("--feature")
    next_task.add_argument("--milestone")
    next_task.set_defaults(handler=command_next)

    claim = commands.add_parser("claim", help="Atomically claim a task and check out its branch.")
    claim.add_argument("task_id", nargs="?")
    claim.add_argument("--next", action="store_true", help="Claim the next available task (retries on races).")
    claim.add_argument("--feature")
    claim.add_argument("--milestone")
    claim.set_defaults(handler=command_claim)

    claim_milestone = commands.add_parser("claim-milestone", help="Atomically claim all open tasks of a milestone.")
    claim_milestone.add_argument("milestone")
    claim_milestone.add_argument("--feature", required=True)
    claim_milestone.set_defaults(handler=command_claim_milestone)

    release = commands.add_parser("release", help="Give up a claim by deleting its remote branch.")
    release.add_argument("task_id")
    release.add_argument("--feature", required=True)
    release.add_argument("--force", action="store_true", help="Release even if the branch has work on it.")
    release.set_defaults(handler=command_release)

    mark_done = commands.add_parser("mark-done", help="Set status: done in the task file (working tree).")
    mark_done.add_argument("task_id")
    mark_done.add_argument("--feature", required=True)
    mark_done.set_defaults(handler=command_mark_done)

    gate = commands.add_parser("gate", help="Check that a feature document is approved (exit 5 if not).")
    gate.add_argument("document", choices=GATED_DOCUMENTS)
    gate.add_argument("--feature", required=True)
    gate.set_defaults(handler=command_gate)

    validate = commands.add_parser("validate", help="Check task files in the working tree for consistency.")
    validate.add_argument("--feature")
    validate.set_defaults(handler=command_validate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except BoardError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
