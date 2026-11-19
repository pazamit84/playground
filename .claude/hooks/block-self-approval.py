#!/usr/bin/env python3
"""PreToolUse hook: only a human may approve a gated document.

Gated documents: docs/features/<feature>/{product,architecture,plan}.md.
The tool call is blocked (exit code 2) when it would leave a gated document with
`status: approved`. That covers two cases:
  * an agent setting `status: approved` itself, and
  * an agent changing an already-approved document without resetting it to `draft`,
    which would silently invalidate the human's approval.
Shell commands that write `status: approved` into a gated document are blocked on a best-effort basis.
"""
import json
import re
import sys
from pathlib import Path

GATED_DOCUMENT_PATTERN = re.compile(r"docs/features/[^/\s]+/(product|architecture|plan)\.md")
APPROVED_STATUS_LINE = re.compile(r"^status:\s*[\"']?approved\b", re.IGNORECASE | re.MULTILINE)
SHELL_APPROVAL_PATTERN = re.compile(r"status:\s*[\"']?approved\b", re.IGNORECASE)
BLOCKED_EXIT_CODE = 2

BLOCK_MESSAGE = (
    "Blocked by the approval gate: {path} would end up with `status: approved`. "
    "Only a human may approve product.md, architecture.md and plan.md. "
    "Agents write `status: draft`, and when changing an approved document they must also set it "
    "back to `status: draft` so that a human re-approves the new version."
)


def frontmatter_of(text: str) -> str:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    return match.group(1) if match else ""


def is_approved(text: str) -> bool:
    return bool(APPROVED_STATUS_LINE.search(frontmatter_of(text)))


def apply_replacement(text: str, edit: dict) -> str:
    old_text, new_text = edit.get("old_string", ""), edit.get("new_string", "")
    if edit.get("replace_all"):
        return text.replace(old_text, new_text)
    return text.replace(old_text, new_text, 1)


def resulting_content(tool_name: str, tool_input: dict, current_text: str) -> str:
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return apply_replacement(current_text, tool_input)
    if tool_name == "MultiEdit":
        for edit in tool_input.get("edits", []):
            current_text = apply_replacement(current_text, edit)
        return current_text
    return current_text


def file_edit_violation(tool_name: str, tool_input: dict) -> str | None:
    path = tool_input.get("file_path", "")
    if not GATED_DOCUMENT_PATTERN.search(path.replace("\\", "/")):
        return None
    document = Path(path)
    current_text = document.read_text() if document.exists() else ""
    if is_approved(resulting_content(tool_name, tool_input, current_text)):
        return path
    return None


def shell_violation(command: str) -> str | None:
    gated_path = GATED_DOCUMENT_PATTERN.search(command)
    if gated_path and SHELL_APPROVAL_PATTERN.search(command):
        return gated_path.group(0)
    return None


def main() -> int:
    hook_input = json.load(sys.stdin)
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {}) or {}
    if tool_name == "Bash":
        violating_path = shell_violation(tool_input.get("command", ""))
    else:
        violating_path = file_edit_violation(tool_name, tool_input)
    if violating_path:
        print(BLOCK_MESSAGE.format(path=violating_path), file=sys.stderr)
        return BLOCKED_EXIT_CODE
    return 0


if __name__ == "__main__":
    sys.exit(main())
