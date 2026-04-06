"""Human-readable response generation for UI output."""

import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..shared.config import SYSTEM_PROMPT
from ..shared.number_format import format_rows_for_display
from ..shared.text_sanitizer import sanitize_markdown_text
from .request_context import build_recent_chat_text, get_llm_for_task


def format_result_preview(result: Dict[str, Any], max_rows: int = 5) -> str:
    rows = result.get("data", [])
    if not isinstance(rows, list) or not rows:
        return "결과 없음"

    preview_rows, _ = format_rows_for_display([row for row in rows[:max_rows] if isinstance(row, dict)])
    return json.dumps(preview_rows, ensure_ascii=False, indent=2)


def build_response_prompt(user_input: str, result: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
    return f"""당신은 제조 데이터 분석 결과를 한국어로 간결하게 설명하는 어시스턴트입니다.

사용자 질문:
{user_input}

최근 대화:
{build_recent_chat_text(chat_history)}

결과 요약:
{result.get('summary', '')}

결과 행 수:
{len(result.get('data', []))}

결과 미리보기:
{format_result_preview(result)}

분석 계획:
{json.dumps(result.get('analysis_plan', {}), ensure_ascii=False)}

작성 규칙:
1. 현재 결과에서 확인되는 사실만 설명한다.
2. 중요한 수치와 기준을 함께 언급한다.
3. 표 전체를 반복하지 말고 핵심만 3~5문장으로 요약한다.
4. 수치 단위나 비교 기준이 있으면 함께 적는다.
5. 한국어로 자연스럽게 작성한다.
"""


def generate_response(user_input: str, result: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
    prompt = build_response_prompt(user_input, result, chat_history)
    try:
        llm = get_llm_for_task("response_summary")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        if isinstance(response.content, str):
            return sanitize_markdown_text(response.content)
        if isinstance(response.content, list):
            joined = "\n".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in response.content)
            return sanitize_markdown_text(joined)
        return sanitize_markdown_text(str(response.content))
    except Exception:
        fallback = f"{result.get('summary', '결과 요약을 생성하지 못했습니다.')} 결과 미리보기만 먼저 제공합니다."
        return sanitize_markdown_text(fallback)
