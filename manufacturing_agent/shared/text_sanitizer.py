"""마크다운 기반 UI에서 LLM 텍스트를 안전하게 보여주기 위한 보조 함수."""

from __future__ import annotations

import re


def _normalize_numeric_tilde_ranges(text: str) -> str:
    """실수로 생긴 이중 물결 범위 표현을 일반 범위 표현으로 바꾼다."""

    normalized = str(text or "")
    normalized = re.sub(r"(?<=\d)\s*~~\s*(?=\d)", "~", normalized)
    normalized = re.sub(r"(?<=\d%)\s*~~\s*(?=\d)", " ~ ", normalized)
    return normalized


def sanitize_markdown_text(text: str) -> str:
    """응답 문자열이 의도치 않게 취소선으로 렌더링되는 일을 막는다.

    모델이 숫자 범위를 쓰다가 `~~` 를 만들면 Streamlit markdown 이 취소선으로 해석한다.
    먼저 숫자 범위에 해당하는 경우를 정상 범위 표현으로 바꾸고,
    남는 `~~` 는 escape 해서 화면에 문자 그대로 보이게 한다.
    """

    sanitized = _normalize_numeric_tilde_ranges(text)
    sanitized = sanitized.replace("~~", r"\~\~")
    return sanitized
