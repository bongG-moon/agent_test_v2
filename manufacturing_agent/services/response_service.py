"""Human-readable response generation for UI output."""

import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..shared.config import SYSTEM_PROMPT
from ..shared.number_format import format_rows_for_display
from .request_context import build_recent_chat_text, get_llm_for_task


def format_result_preview(result: Dict[str, Any], max_rows: int = 5) -> str:
    rows = result.get("data", [])
    if not isinstance(rows, list) or not rows:
        return "?놁쓬"

    preview_rows, _ = format_rows_for_display([row for row in rows[:max_rows] if isinstance(row, dict)])
    return json.dumps(preview_rows, ensure_ascii=False, indent=2)


def build_response_prompt(user_input: str, result: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
    return f"""?ъ슜?먯뿉寃??쒖“ ?곗씠??遺꾩꽍 寃곌낵瑜??ㅻ챸??二쇱꽭??

?ъ슜??吏덈Ц:
{user_input}

理쒓렐 ???
{build_recent_chat_text(chat_history)}

?꾩옱 寃곌낵 ?붿빟:
{result.get('summary', '')}

?꾩옱 寃곌낵 嫄댁닔:
{len(result.get('data', []))}嫄?

?꾩옱 寃곌낵 誘몃━蹂닿린:
{format_result_preview(result)}

遺꾩꽍 怨꾪쉷:
{json.dumps(result.get('analysis_plan', {}), ensure_ascii=False)}

洹쒖튃:
1. 諛섎뱶???꾩옱 寃곌낵 ?뚯씠釉?湲곗??쇰줈留??ㅻ챸?섏꽭??
2. ?먮낯 ?꾩껜 ?곗씠?곕? 蹂?寃껋쿂??留먰븯吏 留덉꽭??
3. 洹몃９?? ?곸쐞 N, ?뺣젹 ?붿껌?대㈃ 洹?寃곌낵 援ъ“瑜?諛붾줈 ?ㅻ챸?섏꽭??
4. 誘몃━蹂닿린??K/M ?⑥쐞瑜??ㅼ떆 ?섎せ ?댁꽍?섏? 留덉꽭??
5. 3~5臾몄옣?쇰줈 吏㏐퀬 紐낇솗?섍쾶 ?듯븯?몄슂.
"""


def generate_response(user_input: str, result: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
    prompt = build_response_prompt(user_input, result, chat_history)
    try:
        llm = get_llm_for_task("response_summary")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        if isinstance(response.content, str):
            return response.content
        if isinstance(response.content, list):
            return "\n".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in response.content)
        return str(response.content)
    except Exception:
        return f"{result.get('summary', '寃곌낵瑜??뺤씤?덉뒿?덈떎.')} ?꾨옒 ?쒕? ?④퍡 ?뺤씤??二쇱꽭??"
