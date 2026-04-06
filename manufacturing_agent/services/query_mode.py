"""Decide whether we should fetch new raw data or reuse the current table."""

import re
from typing import Any, Dict

from ..data.retrieval import pick_retrieval_tools
from ..graph.state import QueryMode
from ..shared.filter_utils import normalize_text
from .request_context import (
    POST_PROCESSING_KEYWORDS,
    collect_current_source_dataset_keys,
    collect_requested_dataset_keys,
    has_current_data,
    has_explicit_filter_change,
    review_query_mode_with_llm,
)


def has_explicit_date_reference(query_text: str) -> bool:
    normalized = normalize_text(query_text)
    if any(token in normalized for token in ["오늘", "어제", "today", "yesterday"]):
        return True
    return bool(re.search(r"\b20\d{6}\b", str(query_text or "")))


def mentions_grouping_expression(query_text: str) -> bool:
    return bool(re.search(r"([\w/\-가-힣]+)\s*(by|기준|별)", str(query_text or ""), flags=re.IGNORECASE))


def needs_post_processing(
    query_text: str,
    extracted_params: Dict[str, Any] | None = None,
    retrieval_plan: Dict[str, Any] | None = None,
) -> bool:
    from ..domain.registry import match_registered_analysis_rules

    extracted_params = extracted_params or {}
    normalized = normalize_text(query_text)

    if retrieval_plan and retrieval_plan.get("needs_post_processing"):
        return True
    if match_registered_analysis_rules(query_text):
        return True
    if extracted_params.get("group_by"):
        return True
    if mentions_grouping_expression(query_text):
        return True
    return any(token in normalized for token in POST_PROCESSING_KEYWORDS)


def looks_like_new_data_request(query_text: str) -> bool:
    normalized = normalize_text(query_text)
    retrieval_keys = pick_retrieval_tools(query_text)
    retrieval_tokens = [
        "생산",
        "목표",
        "불량",
        "설비",
        "가동률",
        "wip",
        "수율",
        "hold",
        "스크랩",
        "레시피",
        "lot",
        "조회",
    ]

    if has_explicit_date_reference(query_text):
        return True
    if len(retrieval_keys) >= 2:
        return True
    if retrieval_keys and any(token in normalized for token in ["조회", "데이터", "현황", "새로"]):
        return True
    return any(token in normalized for token in retrieval_tokens) and not needs_post_processing(query_text)


def prune_followup_params(user_input: str, extracted_params: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_text(user_input)
    cleaned = dict(extracted_params or {})
    filter_fields = [
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
    ]
    explicit_filter_intent = any(
        token in normalized
        for token in [
            "조건",
            "필터",
            "공정",
            "공정번호",
            "oper",
            "pkg",
            "라인",
            "mode",
            "den",
            "tech",
            "lead",
            "mcp",
        ]
    )
    if not explicit_filter_intent:
        for field in filter_fields:
            cleaned[field] = None
    return cleaned


def choose_query_mode(
    user_input: str,
    current_data: Dict[str, Any] | None,
    extracted_params: Dict[str, Any],
) -> QueryMode:
    """Choose between fresh retrieval and follow-up transformation."""

    if not has_current_data(current_data):
        return "retrieval"

    requested_dataset_keys = collect_requested_dataset_keys(user_input)
    current_dataset_keys = collect_current_source_dataset_keys(current_data)

    if requested_dataset_keys and not set(requested_dataset_keys).issubset(set(current_dataset_keys)):
        return "retrieval"

    if has_explicit_filter_change(user_input, extracted_params, current_data):
        return "retrieval"

    if not looks_like_new_data_request(user_input):
        return "followup_transform"

    if requested_dataset_keys and set(requested_dataset_keys).issubset(set(current_dataset_keys)):
        return review_query_mode_with_llm(user_input, current_data, extracted_params, requested_dataset_keys)

    return "retrieval"
