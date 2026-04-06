"""Helpers for rendering LLM text safely in markdown-based UIs."""

from __future__ import annotations

import re


def _normalize_numeric_tilde_ranges(text: str) -> str:
    """Turn accidental double-tilde numeric ranges into a normal range marker."""

    normalized = str(text or "")
    normalized = re.sub(r"(?<=\d)\s*~~\s*(?=\d)", "~", normalized)
    normalized = re.sub(r"(?<=\d%)\s*~~\s*(?=\d)", " ~ ", normalized)
    return normalized


def sanitize_markdown_text(text: str) -> str:
    """Prevent accidental markdown strikethrough in assistant responses.

    The assistant sometimes emits `~~` while trying to express numeric ranges.
    Streamlit markdown interprets that as strikethrough. We normalize numeric
    range cases first, then escape any remaining `~~` so the UI shows text
    literally instead of crossing it out.
    """

    sanitized = _normalize_numeric_tilde_ranges(text)
    sanitized = sanitized.replace("~~", r"\~\~")
    return sanitized
