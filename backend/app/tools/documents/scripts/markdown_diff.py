from __future__ import annotations

from difflib import unified_diff


def markdown_diff_preview(before: str, after: str) -> str:
    if before == after:
        return "No changes"
    return f"- before: {len(before)} chars\n- after: {len(after)} chars"


def unified_markdown_diff(
    *,
    before: str,
    after: str,
    fromfile: str = "a/document.md",
    tofile: str = "b/document.md",
) -> str:
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    lines = list(unified_diff(before_lines, after_lines, fromfile=fromfile, tofile=tofile, lineterm=""))
    return "\n".join(lines)

