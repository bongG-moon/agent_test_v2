"""Shared request and result helpers used across graph nodes.

This module holds small, reusable functions that explain the current request
or normalize retrieval/analysis results. Keeping them here prevents the graph
file from becoming a giant utility dump.
"""

import json
import re
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..data.retrieval import DATASET_REGISTRY, get_dataset_label, list_available_dataset_labels, pick_retrieval_tools
from ..domain.registry import (
    build_registered_domain_prompt,
    get_dataset_keyword_map,
    match_registered_analysis_rules,
)
from ..graph.state import QueryMode
from ..shared.config import SYSTEM_PROMPT, get_llm
from ..shared.filter_utils import normalize_text


APPLIED_PARAM_FIELDS = [
    "date",
    "process_name",
    "oper_num",
    "pkg_type1",
    "pkg_type2",
    "product_name",
    "line_name",
    "mode",
    "den",
    "tech",
    "lead",
    "mcp_no",
    "group_by",
]

POST_PROCESSING_KEYWORDS = [
    "?곸쐞",
    "?섏쐞",
    "?뺣젹",
    "鍮꾧탳",
    "李⑥씠",
    "?붿빟",
    "?됯퇏",
    "?⑷퀎",
    "鍮꾩쑉",
    "?ъ꽦瑜?",
    "異붿씠",
    "?쒖쐞",
    "紐⑸줉",
    "list",
    "?녿뒗",
    "top",
    "rank",
    "group by",
]


def get_llm_for_task(task: str, temperature: float = 0.0):
    """Return an LLM client while staying compatible with simple monkeypatches."""

    try:
        return get_llm(task=task, temperature=temperature)
    except TypeError:
        try:
            return get_llm(temperature=temperature)
        except TypeError:
            return get_llm()


def build_recent_chat_text(chat_history: List[Dict[str, str]], max_messages: int = 6) -> str:
    if not chat_history:
        return "(?댁쟾 ????놁쓬)"

    lines = []
    for message in chat_history[-max_messages:]:
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"- {message.get('role', 'unknown')}: {content}")
    return "\n".join(lines) if lines else "(?댁쟾 ????놁쓬)"


def get_current_table_columns(current_data: Dict[str, Any] | None) -> List[str]:
    if not isinstance(current_data, dict):
        return []

    rows = current_data.get("data", [])
    if not isinstance(rows, list):
        return []

    columns = set()
    for row in rows:
        if isinstance(row, dict):
            columns.update(row.keys())
    return sorted(columns)


def has_current_data(current_data: Dict[str, Any] | None) -> bool:
    return bool(isinstance(current_data, dict) and isinstance(current_data.get("data"), list) and current_data.get("data"))


def raw_dataset_key(dataset_key: str) -> str:
    return str(dataset_key or "").split("__", 1)[0]


def collect_applied_params(extracted_params: Dict[str, Any]) -> Dict[str, Any]:
    return {field: extracted_params.get(field) for field in APPLIED_PARAM_FIELDS if extracted_params.get(field)}


def attach_result_metadata(result: Dict[str, Any], extracted_params: Dict[str, Any], original_tool_name: str) -> Dict[str, Any]:
    if result.get("success"):
        result["original_tool_name"] = original_tool_name
        result["applied_params"] = collect_applied_params(extracted_params)
        if "source_dataset_keys" not in result:
            dataset_key = str(result.get("dataset_key", "")).strip()
            result["source_dataset_keys"] = [raw_dataset_key(dataset_key)] if dataset_key else []
        result["available_columns"] = get_current_table_columns(result)
    return result


def collect_current_source_dataset_keys(current_data: Dict[str, Any] | None) -> List[str]:
    if not isinstance(current_data, dict):
        return []

    explicit_keys = [raw_dataset_key(item) for item in current_data.get("source_dataset_keys", []) if item]
    if explicit_keys:
        return list(dict.fromkeys(explicit_keys))

    current_datasets = current_data.get("current_datasets", [])
    if isinstance(current_datasets, list):
        dataset_keys = [
            raw_dataset_key(str(item.get("dataset_key", "")))
            for item in current_datasets
            if isinstance(item, dict) and item.get("dataset_key")
        ]
        if dataset_keys:
            return list(dict.fromkeys(dataset_keys))

    dataset_key = str(current_data.get("dataset_key", "")).strip()
    if dataset_key:
        return [raw_dataset_key(dataset_key)]
    return []


def collect_requested_dataset_keys(user_input: str) -> List[str]:
    dataset_keys = [key for key in pick_retrieval_tools(user_input) if key in DATASET_REGISTRY]
    for rule in match_registered_analysis_rules(user_input):
        for dataset_key in rule.get("required_datasets", []):
            if dataset_key in DATASET_REGISTRY and dataset_key not in dataset_keys:
                dataset_keys.append(dataset_key)
    return dataset_keys


def normalize_filter_value(value: Any) -> Any:
    if isinstance(value, list):
        return sorted(str(item) for item in value)
    return str(value) if value not in (None, "", []) else None


def user_explicitly_mentions_filter(field_name: str, user_input: str) -> bool:
    normalized = normalize_text(user_input)
    keyword_map = {
        "date": ["?ㅻ뒛", "?댁젣", "date", "?쇱옄", "?좎쭨"],
        "process_name": ["怨듭젙", "process", "wb", "da", "wet", "lt", "bg", "hs", "ws", "sat", "fcb"],
        "oper_num": ["oper", "怨듭젙踰덊샇", "operation"],
        "pkg_type1": ["pkg", "fcbga", "lfbga"],
        "pkg_type2": ["stack", "odp", "16dp", "sdp"],
        "product_name": ["?쒗뭹", "product", "hbm", "3ds", "auto"],
        "line_name": ["?쇱씤", "line"],
        "mode": ["mode", "ddr", "lpddr"],
        "den": ["den", "?⑸웾", "256g", "512g", "1t"],
        "tech": ["tech", "lc", "fo", "fc"],
        "lead": ["lead"],
        "mcp_no": ["mcp"],
    }
    return any(token in normalized for token in keyword_map.get(field_name, []))


def has_explicit_filter_change(user_input: str, extracted_params: Dict[str, Any], current_data: Dict[str, Any] | None) -> bool:
    current_filters = {}
    if isinstance(current_data, dict):
        current_filters = current_data.get("applied_params", {}) or {}

    for field_name in APPLIED_PARAM_FIELDS:
        if field_name == "group_by":
            continue
        new_value = extracted_params.get(field_name)
        current_value = current_filters.get(field_name)
        if normalize_filter_value(new_value) == normalize_filter_value(current_value):
            continue
        if new_value and user_explicitly_mentions_filter(field_name, user_input):
            return True
    return False


def build_current_data_profile(current_data: Dict[str, Any] | None) -> Dict[str, Any]:
    return {
        "tool_name": str((current_data or {}).get("tool_name", "")),
        "source_dataset_keys": collect_current_source_dataset_keys(current_data),
        "applied_params": dict((current_data or {}).get("applied_params", {}) or {}),
        "columns": get_current_table_columns(current_data),
    }


def attach_source_dataset_metadata(result: Dict[str, Any], source_results: List[Dict[str, Any]]) -> None:
    result["source_dataset_keys"] = list(
        dict.fromkeys(
            raw_dataset_key(str(item.get("dataset_key", "")))
            for item in source_results
            if item.get("dataset_key")
        )
    )


def review_query_mode_with_llm(
    user_input: str,
    current_data: Dict[str, Any] | None,
    extracted_params: Dict[str, Any],
    requested_dataset_keys: List[str],
) -> QueryMode:
    if not has_current_data(current_data):
        return "retrieval"

    profile = build_current_data_profile(current_data)
    prompt = f"""You are deciding whether a manufacturing follow-up question should reuse the current table
or fetch fresh source data. Return JSON only.

Rules:
- Choose `retrieval` when the user is asking for a different raw dataset, a different process/date/product filter,
  or a new source table that is not already included in the current result.
- Choose `followup_transform` when the current table is enough and the user is mainly asking for grouping,
  sorting, ranking, filtering, comparison, or a light recomputation on the same scope.

User question:
{user_input}

Current table profile:
{json.dumps(profile, ensure_ascii=False)}

Extracted filters:
{json.dumps(collect_applied_params(extracted_params), ensure_ascii=False)}

Requested dataset keys:
{json.dumps(requested_dataset_keys, ensure_ascii=False)}

Return only:
{{
  "query_mode": "retrieval",
  "reason": "short reason"
}}"""

    try:
        llm = get_llm_for_task("query_mode_review")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        parsed = parse_json_block(extract_text_from_response(response.content))
        if parsed.get("query_mode") == "followup_transform":
            return "followup_transform"
    except Exception:
        pass

    return "retrieval"


def build_unknown_retrieval_message() -> str:
    available_labels = list_available_dataset_labels()
    if not available_labels:
        return "議고쉶 媛?ν븳 ?곗씠?곗뀑 ?뺣낫瑜??꾩쭅 遺덈윭?ㅼ? 紐삵뻽?듬땲?? 吏덈Ц ?쒗쁽??議곌툑 ??援ъ껜?곸쑝濡?諛붽퓭 二쇱꽭??"
    return "?대뼡 ?곗씠?곕? 議고쉶?좎? ?꾩쭅 ?먮떒?섏? 紐삵뻽?듬땲?? ?꾩옱 ?깅줉??議고쉶 ??곸? " + ", ".join(available_labels) + " ?낅땲??"


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


def parse_json_block(text: str) -> Dict[str, Any]:
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


def build_dataset_catalog_text() -> str:
    lines: List[str] = []
    keyword_map = get_dataset_keyword_map()
    for dataset_key, meta in DATASET_REGISTRY.items():
        keywords = ", ".join(str(keyword) for keyword in keyword_map.get(dataset_key, meta.get("keywords", [])))
        lines.append(f"- {dataset_key}: label={meta.get('label', dataset_key)}, keywords={keywords}")
    return "\n".join(lines)


def get_dataset_labels_for_message(dataset_keys: List[str]) -> List[str]:
    return [get_dataset_label(key) for key in dataset_keys]
