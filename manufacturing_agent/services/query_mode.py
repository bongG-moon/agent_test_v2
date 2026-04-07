"""질문을 새 조회로 처리할지, 현재 테이블 후처리로 처리할지 판단하는 서비스."""

import re
from typing import Any, Dict

from ..data.retrieval import pick_retrieval_tools
from ..domain.knowledge import QUERY_MODE_SIGNAL_SPECS
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


def _matches_query_mode_signal(query_text: str, signal_name: str) -> bool:
    """도메인에 정의된 query mode 신호 스펙으로 표현을 감지한다."""

    signal_spec = QUERY_MODE_SIGNAL_SPECS.get(signal_name, {})
    normalized = normalize_text(query_text)

    if any(token in normalized for token in signal_spec.get("keywords", [])):
        return True

    return any(
        re.search(pattern, str(query_text or ""), flags=re.IGNORECASE)
        for pattern in signal_spec.get("patterns", [])
    )


def has_explicit_date_reference(query_text: str) -> bool:
    """질문 안에 날짜가 직접 언급됐는지 확인한다."""

    return _matches_query_mode_signal(query_text, "explicit_date_reference")


def mentions_grouping_expression(query_text: str) -> bool:
    """`MODE별`, `공정 기준`, `by line` 같은 그룹화 의도를 찾는다."""

    return _matches_query_mode_signal(query_text, "grouping_expression")


def needs_post_processing(
    query_text: str,
    extracted_params: Dict[str, Any] | None = None,
    retrieval_plan: Dict[str, Any] | None = None,
) -> bool:
    """조회 후에 pandas 후처리가 필요한 질문인지 판단한다."""

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
    """사용자 의도가 새 원천 데이터를 가져오는 쪽에 가까운지 판단한다."""

    retrieval_keys = pick_retrieval_tools(query_text)

    if has_explicit_date_reference(query_text):
        return True
    if len(retrieval_keys) >= 2:
        return True
    if retrieval_keys and _matches_query_mode_signal(query_text, "fresh_retrieval_hint"):
        return True
    return _matches_query_mode_signal(query_text, "retrieval_request") and not needs_post_processing(query_text)


def prune_followup_params(user_input: str, extracted_params: Dict[str, Any]) -> Dict[str, Any]:
    """후속 분석에서 꼭 필요하지 않은 필터만 남기고 나머지는 걷어낸다."""

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
    explicit_filter_intent = _matches_query_mode_signal(user_input, "followup_filter_intent")
    if not explicit_filter_intent:
        for field in filter_fields:
            cleaned[field] = None
    return cleaned


def choose_query_mode(
    user_input: str,
    current_data: Dict[str, Any] | None,
    extracted_params: Dict[str, Any],
) -> QueryMode:
    """질문을 `retrieval`과 `followup_transform` 중 어디로 보낼지 결정한다."""

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
