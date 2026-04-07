"""안전한 pandas 후속 분석 코드를 만들기 위한 LLM 프롬프트 빌더."""

import json
from typing import Any, Dict, List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage

from .contracts import PreprocessPlan
from .helpers import dataset_profile
from ..domain.knowledge import build_domain_knowledge_prompt
from ..domain.registry import (
    build_registered_domain_prompt,
    format_analysis_rule_for_prompt,
    match_registered_analysis_rules,
)
from ..shared.config import get_llm


def _get_llm_for_task(task: str):
    try:
        return get_llm(task=task)
    except TypeError:
        return get_llm()


def build_dataset_specific_hints(data: List[Dict[str, Any]], query_text: str) -> str:
    """현재 컬럼에 맞는 짧은 힌트를 추가해 생성 코드의 안정성을 높인다."""

    if not data:
        return ""

    columns = {str(key) for key in data[0].keys()}
    lower_query = str(query_text or "").lower()
    hints: List[str] = []

    if "yield_rate" in columns:
        hints.append("- Use `yield_rate` for yield-focused questions unless the user explicitly asks for pass/test counts.")
    if "dominant_fail_bin" in columns:
        hints.append("- Use `dominant_fail_bin` for major defect or fail-bin summaries.")
    if "hold_reason" in columns:
        hints.append("- Use `hold_reason` for representative hold-reason questions.")
    if "lot_id" in columns:
        hints.append("- Count `lot_id` when the user asks for lot count.")
    if "hold_qty" in columns:
        hints.append("- Sum `hold_qty` for hold quantity questions.")
    if "hold_hours" in columns:
        hints.append("- Average `hold_hours` for average hold-time questions.")
    if "avg_wait_minutes" in columns:
        hints.append("- Average `avg_wait_minutes` for waiting-time questions.")
    if "상태" in columns:
        hints.append("- Use `상태` for status or abnormal-state summaries.")
    if "defect_rate" in columns:
        hints.append("- Prefer `defect_rate` for defect-rate questions.")
    if "주요불량유형" in columns:
        hints.append("- Use `주요불량유형` when the user asks for the top defect case.")
    if "production" in columns and "target" in columns and ("achievement" in lower_query or "달성" in query_text or "목표" in query_text):
        hints.append("- Calculate achievement rate as `production / target`.")
    if "avg_wait_minutes" in columns and "상태" in columns and "hold lot" in lower_query:
        hints.append("- If both average wait time and hold-lot count are requested, include them in the same grouped table.")

    return "\n".join(hints)


def extract_text_from_response(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content)


def extract_json_payload(text: str) -> Dict[str, Any]:
    cleaned = str(text or "").strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0]

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        return json.loads(cleaned[start : end + 1])
    except Exception:
        return {}


def build_llm_prompt(
    query_text: str,
    data: List[Dict[str, Any]],
    retry_error: str = "",
    previous_code: str = "",
) -> str:
    profile = dataset_profile(data)
    dataset_hints = build_dataset_specific_hints(data, query_text)
    matched_rules = match_registered_analysis_rules(query_text)
    matched_rule_lines = [format_analysis_rule_for_prompt(rule) for rule in matched_rules]
    retry_section = ""
    if retry_error:
        retry_section = f"""
Previous generated code failed.
Failure reason:
{retry_error}

Previous code:
{previous_code}

Write corrected pandas transformation code.
"""

    return f"""You generate pandas code for follow-up analysis on an already retrieved manufacturing dataframe.
Return JSON only.

Rules:
- Work only on dataframe `df`.
- Always assign the final DataFrame to `result`.
- Do not import anything.
- Do not use files, network, shell, eval, exec, OS APIs, plotting, or database access.
- Use only pandas operations on existing columns.
- Never invent missing columns.
- If the user requests a missing column, leave code empty and add a warning.
- Keep the code concise and readable.
- If grouping, sorting, filtering, ranking, or derived columns are needed, express them directly in code.
- If a matched custom rule includes `source_columns`, `condition`, `decision_rule`, `output_column`, or `default_group_by`,
  use them as strong hints.

Manufacturing domain hints:
{build_domain_knowledge_prompt()}

Custom domain registry:
{build_registered_domain_prompt()}

Matched derived-metric rules for this question:
{chr(10).join(matched_rule_lines) if matched_rule_lines else "- No matched custom rule."}

Dataset profile:
{json.dumps(profile, ensure_ascii=False)}

Dataset-specific column hints:
{dataset_hints or "- No extra dataset-specific hints."}

User question:
{query_text}
{retry_section}

Helpful examples:
- Achievement rate:
  grouped = df.groupby('OPER_NAME', as_index=False).agg(production=('production', 'sum'), target=('target', 'sum'))
  grouped['achievement_rate'] = grouped['production'] / grouped['target']
  result = grouped
- Status flag:
  result = df.copy()
  result['hold_abnormal_flag'] = result['상태'].isin(['HOLD', 'REWORK']).map({{True: 'abnormal', False: 'normal'}})

Return this schema:
{{
  "intent": "short summary",
  "operations": ["groupby", "sort_values"],
  "output_columns": ["MODE", "production"],
  "group_by_columns": ["MODE"],
  "partition_by_columns": [],
  "filters": [],
  "sort_by": "production",
  "sort_order": "desc",
  "top_n": 5,
  "top_n_per_group": 3,
  "metric_column": "production",
  "warnings": [],
  "code": "result = df.copy()"
}}
"""


def build_llm_plan(
    query_text: str,
    data: List[Dict[str, Any]],
    retry_error: str = "",
    previous_code: str = "",
) -> Tuple[PreprocessPlan | None, str]:
    try:
        llm = _get_llm_for_task("analysis_retry" if retry_error else "analysis_code")
        prompt = build_llm_prompt(query_text, data, retry_error=retry_error, previous_code=previous_code)
        response = llm.invoke(
            [
                SystemMessage(content="Generate safe pandas dataframe transformation code."),
                HumanMessage(content=prompt),
            ]
        )
        parsed = extract_json_payload(extract_text_from_response(response.content))
        code = str(parsed.get("code", "") or "").strip()

        plan: PreprocessPlan = {
            "intent": str(parsed.get("intent", "current data preprocessing")).strip() or "current data preprocessing",
            "operations": [str(item).strip() for item in (parsed.get("operations") or []) if str(item).strip()],
            "output_columns": [str(item).strip() for item in (parsed.get("output_columns") or []) if str(item).strip()],
            "group_by_columns": [str(item).strip() for item in (parsed.get("group_by_columns") or []) if str(item).strip()],
            "partition_by_columns": [str(item).strip() for item in (parsed.get("partition_by_columns") or []) if str(item).strip()],
            "filters": parsed.get("filters") or [],
            "sort_by": str(parsed.get("sort_by", "")).strip(),
            "sort_order": str(parsed.get("sort_order", "")).strip() or "desc",
            "metric_column": str(parsed.get("metric_column", "")).strip(),
            "warnings": [str(item).strip() for item in (parsed.get("warnings") or []) if str(item).strip()],
            "code": code,
            "source": "llm_primary" if not retry_error else "llm_retry",
        }
        if isinstance(parsed.get("top_n"), int):
            plan["top_n"] = parsed["top_n"]
        if isinstance(parsed.get("top_n_per_group"), int):
            plan["top_n_per_group"] = parsed["top_n_per_group"]

        if not code:
            return None, "llm_empty_code"
        return plan, "llm_primary" if not retry_error else "llm_retry"
    except Exception:
        return None, "llm_failed"
