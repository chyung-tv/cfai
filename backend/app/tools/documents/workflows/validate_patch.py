from __future__ import annotations

import re

LEDGER_DOC_KEY = "portfolio_ledger"
MAX_PATCH_CHARS = 120_000

_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


class DocumentPatchValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _split_table_cells(row: str) -> list[str]:
    stripped = row.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _extract_markdown_tables(content: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = content.splitlines()
    tables: list[tuple[list[str], list[list[str]]]] = []
    i = 0
    while i < len(lines) - 1:
        header = lines[i]
        separator = lines[i + 1]
        if "|" not in header or not _TABLE_SEPARATOR_RE.match(separator):
            i += 1
            continue
        headers = _split_table_cells(header)
        rows: list[list[str]] = []
        i += 2
        while i < len(lines) and "|" in lines[i] and lines[i].strip():
            rows.append(_split_table_cells(lines[i]))
            i += 1
        tables.append((headers, rows))
    return tables


def validate_patch(patch: str) -> None:
    raw = (patch or "").strip()
    if not raw:
        raise DocumentPatchValidationError("empty_patch", "Patch is empty.")
    if len(raw) > MAX_PATCH_CHARS:
        raise DocumentPatchValidationError("patch_too_large", "Patch exceeds maximum allowed size.")

    lines = raw.splitlines()
    has_old_header = any(line.startswith("--- ") for line in lines)
    has_new_header = any(line.startswith("+++ ") for line in lines)
    has_hunk = any(line.startswith("@@ ") or line == "@@" for line in lines)
    if not (has_old_header and has_new_header and has_hunk):
        raise DocumentPatchValidationError(
            "invalid_patch_format",
            "Patch must be unified diff format and include '---', '+++', and '@@' lines.",
        )


def validate_document_content(*, doc_key: str, content: str) -> None:
    if not doc_key.strip():
        raise DocumentPatchValidationError("invalid_doc_key", "Document key is required.")
    is_ledger_like = "ledger" in doc_key.lower()
    if not is_ledger_like:
        return

    tables = _extract_markdown_tables(content)
    symbol_table_found = False
    seen_symbols: set[str] = set()
    for headers, rows in tables:
        normalized_headers = [header.strip().lower() for header in headers]
        if "symbol" not in normalized_headers:
            continue
        symbol_table_found = True
        symbol_index = normalized_headers.index("symbol")
        for row in rows:
            if len(row) != len(headers):
                raise DocumentPatchValidationError(
                    "row_column_mismatch",
                    "Table rows must have the same number of columns as the header.",
                )
            symbol = (row[symbol_index] if symbol_index < len(row) else "").strip()
            if not symbol:
                raise DocumentPatchValidationError("empty_symbol_value", "Each table row must include a Symbol value.")
            symbol_key = symbol.casefold()
            if symbol_key in seen_symbols:
                raise DocumentPatchValidationError("duplicate_symbol", f"Duplicate Symbol detected: {symbol}.")
            seen_symbols.add(symbol_key)

    if not symbol_table_found:
        raise DocumentPatchValidationError(
            "missing_symbol_column",
            "Portfolio ledger must contain at least one markdown table with a Symbol column.",
        )


def is_patch_valid(patch: str) -> bool:
    try:
        validate_patch(patch)
        return True
    except DocumentPatchValidationError:
        return False

