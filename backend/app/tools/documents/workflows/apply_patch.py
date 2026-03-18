from __future__ import annotations

import re

from app.tools.documents.workflows.validate_patch import (
    DocumentPatchValidationError,
    validate_document_content,
    validate_patch,
)

_HUNK_RE = re.compile(r"^@@\s*-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s*@@")


class DocumentPatchApplyError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _normalize_lines(text: str) -> list[str]:
    return text.splitlines()


def _join_lines(lines: list[str], had_trailing_newline: bool) -> str:
    text = "\n".join(lines)
    if had_trailing_newline and text:
        return text + "\n"
    return text


def _parse_hunk_header(line: str) -> tuple[int, int]:
    match = _HUNK_RE.match(line)
    if not match:
        raise DocumentPatchApplyError("invalid_hunk_header", f"Invalid hunk header: {line}")
    old_start = int(match.group(1))
    old_count = int(match.group(2) or "1")
    return old_start, old_count


def _apply_unified_diff(original: str, patch: str) -> str:
    original_lines = _normalize_lines(original)
    had_trailing_newline = original.endswith("\n")
    patch_lines = patch.splitlines()
    output: list[str] = []
    cursor = 0
    i = 0

    while i < len(patch_lines) and not patch_lines[i].startswith("@@"):
        i += 1
    if i >= len(patch_lines):
        raise DocumentPatchApplyError("missing_hunks", "Unified diff must include at least one hunk.")

    while i < len(patch_lines):
        line = patch_lines[i]
        if not line.startswith("@@"):
            i += 1
            continue
        old_start, old_count = _parse_hunk_header(line)
        target_index = max(old_start - 1, 0)
        if target_index < cursor:
            raise DocumentPatchApplyError("overlapping_hunks", "Patch hunks overlap and cannot be applied.")

        output.extend(original_lines[cursor:target_index])
        cursor = target_index
        i += 1
        removed = 0
        while i < len(patch_lines) and not patch_lines[i].startswith("@@"):
            hunk_line = patch_lines[i]
            if not hunk_line:
                prefix = " "
                payload = ""
            else:
                prefix = hunk_line[0]
                payload = hunk_line[1:]
            if prefix == "\\":
                i += 1
                continue
            if prefix == " ":
                if cursor >= len(original_lines) or original_lines[cursor] != payload:
                    raise DocumentPatchApplyError(
                        "context_mismatch",
                        "Patch context does not match current document content.",
                    )
                output.append(original_lines[cursor])
                cursor += 1
            elif prefix == "-":
                if cursor >= len(original_lines) or original_lines[cursor] != payload:
                    raise DocumentPatchApplyError(
                        "delete_mismatch",
                        "Patch delete operation does not match current document content.",
                    )
                cursor += 1
                removed += 1
            elif prefix == "+":
                output.append(payload)
            else:
                raise DocumentPatchApplyError("invalid_hunk_line", f"Invalid patch hunk line: {hunk_line}")
            i += 1
        if old_count and removed > old_count:
            raise DocumentPatchApplyError("invalid_delete_count", "Patch hunk removes more lines than declared.")

    output.extend(original_lines[cursor:])
    return _join_lines(output, had_trailing_newline)


def apply_document_patch(original: str, patch: str, *, doc_key: str) -> str:
    try:
        validate_patch(patch)
        patched = _apply_unified_diff(original, patch)
        validate_document_content(doc_key=doc_key, content=patched)
        return patched
    except DocumentPatchValidationError as exc:
        raise DocumentPatchApplyError(exc.code, exc.message) from exc

