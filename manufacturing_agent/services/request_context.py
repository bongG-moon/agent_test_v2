"""그래프 노드들이 공통으로 쓰는 요청/결과 보조 함수 모음.

이 파일의 목적은 다음 두 가지다.

1. 현재 질문과 이전 결과를 해석할 때 반복되는 작은 로직을 모아 둔다.
2. 그래프 노드 파일이 너무 커지지 않도록, 맥락 관련 유틸리티를 분리한다.
"""

import json
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
    "비교",
    "정렬",
    "순위",
    "상위",
    "하위",
    "요약",
    "집계",
    "그룹",
    "그룹핑",
    "목록",
    "추세",
    "분석",
    "기준",
    "별",
    "list",
    "top",
    "rank",
    "group by",
]


def get_llm_for_task(task: str, temperature: float = 0.0):
    """모델 생성 함수를 안전하게 감싼다.

    테스트에서는 `get_llm` 이 단순 monkeypatch 로 바뀌는 경우가 많아서
    인자 시그니처가 조금 달라도 동작하도록 방어적으로 작성했다.
    """

    try:
        return get_llm(task=task, temperature=temperature)
    except TypeError:
        try:
            return get_llm(temperature=temperature)
        except TypeError:
            return get_llm()


def build_recent_chat_text(chat_history: List[Dict[str, str]], max_messages: int = 6) -> str:
    """최근 대화를 사람이 읽기 쉬운 텍스트로 압축한다."""

    if not chat_history:
        return "(최근 대화 없음)"

    lines = []
    for message in chat_history[-max_messages:]:
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"- {message.get('role', 'unknown')}: {content}")
    return "\n".join(lines) if lines else "(최근 대화 없음)"


def get_current_table_columns(current_data: Dict[str, Any] | None) -> List[str]:
    """현재 결과 테이블에 어떤 컬럼이 있는지 모아 반환한다."""

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
    """현재 테이블이 실제로 존재하는지 빠르게 확인한다."""

    return bool(isinstance(current_data, dict) and isinstance(current_data.get("data"), list) and current_data.get("data"))


def raw_dataset_key(dataset_key: str) -> str:
    """`production__today` 같은 키에서 원본 데이터셋 키만 꺼낸다."""

    return str(dataset_key or "").split("__", 1)[0]


def collect_applied_params(extracted_params: Dict[str, Any]) -> Dict[str, Any]:
    """파라미터 추출 결과 중 실제로 값이 있는 필드만 남긴다."""

    return {field: extracted_params.get(field) for field in APPLIED_PARAM_FIELDS if extracted_params.get(field)}


def attach_result_metadata(result: Dict[str, Any], extracted_params: Dict[str, Any], original_tool_name: str) -> Dict[str, Any]:
    """결과 딕셔너리에 추적용 메타데이터를 붙인다.

    이후 follow-up 질문에서 "이 결과가 어떤 조건으로 조회됐는지" 판단할 때 사용한다.
    """

    if result.get("success"):
        result["original_tool_name"] = original_tool_name
        result["applied_params"] = collect_applied_params(extracted_params)
        if "source_dataset_keys" not in result:
            dataset_key = str(result.get("dataset_key", "")).strip()
            result["source_dataset_keys"] = [raw_dataset_key(dataset_key)] if dataset_key else []
        result["available_columns"] = get_current_table_columns(result)
    return result


def collect_current_source_dataset_keys(current_data: Dict[str, Any] | None) -> List[str]:
    """현재 결과가 어떤 원천 데이터셋에서 왔는지 추적한다."""

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
    """질문이 필요로 하는 데이터셋 후보를 모은다.

    기본 키워드 매칭 결과에 더해, 사용자 정의 분석 규칙이 요구하는 데이터셋도 같이 포함한다.
    """

    dataset_keys = [key for key in pick_retrieval_tools(user_input) if key in DATASET_REGISTRY]
    for rule in match_registered_analysis_rules(user_input):
        for dataset_key in rule.get("required_datasets", []):
            if dataset_key in DATASET_REGISTRY and dataset_key not in dataset_keys:
                dataset_keys.append(dataset_key)
    return dataset_keys


def normalize_filter_value(value: Any) -> Any:
    """필터 비교를 쉽게 하기 위해 값을 문자열/정렬 리스트 형태로 맞춘다."""

    if isinstance(value, list):
        return sorted(str(item) for item in value)
    return str(value) if value not in (None, "", []) else None


def user_explicitly_mentions_filter(field_name: str, user_input: str) -> bool:
    """사용자가 특정 필터를 직접 언급했는지 확인한다."""

    normalized = normalize_text(user_input)
    keyword_map = {
        "date": ["오늘", "어제", "date", "일자", "날짜"],
        "process_name": ["공정", "process", "wb", "da", "wet", "lt", "bg", "hs", "ws", "sat", "fcb"],
        "oper_num": ["oper", "공정번호", "operation"],
        "pkg_type1": ["pkg", "fcbga", "lfbga"],
        "pkg_type2": ["stack", "odp", "16dp", "sdp"],
        "product_name": ["제품", "product", "hbm", "3ds", "auto"],
        "line_name": ["라인", "line"],
        "mode": ["mode", "ddr", "lpddr"],
        "den": ["den", "용량", "256g", "512g", "1t"],
        "tech": ["tech", "lc", "fo", "fc"],
        "lead": ["lead"],
        "mcp_no": ["mcp"],
    }
    return any(token in normalized for token in keyword_map.get(field_name, []))


def has_explicit_filter_change(user_input: str, extracted_params: Dict[str, Any], current_data: Dict[str, Any] | None) -> bool:
    """현재 결과와 비교했을 때 사용자가 새 필터를 요구했는지 판단한다."""

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
    """현재 테이블 상태를 LLM 검토에 넘기기 좋은 작은 요약으로 만든다."""

    return {
        "tool_name": str((current_data or {}).get("tool_name", "")),
        "source_dataset_keys": collect_current_source_dataset_keys(current_data),
        "applied_params": dict((current_data or {}).get("applied_params", {}) or {}),
        "columns": get_current_table_columns(current_data),
    }


def attach_source_dataset_metadata(result: Dict[str, Any], source_results: List[Dict[str, Any]]) -> None:
    """최종 결과에 원천 데이터셋 목록을 붙인다."""

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
    """규칙만으로 애매할 때 LLM에게 마지막 판단을 맡긴다.

    이미 현재 데이터가 충분해 보일 때만 호출한다.
    즉, 명확하게 새 조회가 필요한 경우에는 이 함수까지 오지 않는다.
    """

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
    """어떤 데이터셋을 봐야 할지 찾지 못했을 때의 안내 문구를 만든다."""

    available_labels = list_available_dataset_labels()
    if not available_labels:
        return "질문과 맞는 데이터셋을 바로 찾지 못했습니다. 어떤 데이터를 보고 싶은지 조금 더 구체적으로 말씀해 주세요."
    return "질문과 맞는 데이터셋을 바로 찾지 못했습니다. 현재 조회 가능한 데이터는 " + ", ".join(available_labels) + " 입니다."


def extract_text_from_response(content: Any) -> str:
    """LLM 응답이 문자열/리스트 어느 형태든 텍스트로 평탄화한다."""

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
    """마크다운 코드블록이 섞여 있어도 JSON 객체만 꺼내 파싱한다."""

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
    """등록된 데이터셋과 키워드 목록을 LLM 프롬프트용 텍스트로 만든다."""

    lines: List[str] = []
    keyword_map = get_dataset_keyword_map()
    for dataset_key, meta in DATASET_REGISTRY.items():
        keywords = ", ".join(str(keyword) for keyword in keyword_map.get(dataset_key, meta.get("keywords", [])))
        lines.append(f"- {dataset_key}: label={meta.get('label', dataset_key)}, keywords={keywords}")
    return "\n".join(lines)


def get_dataset_labels_for_message(dataset_keys: List[str]) -> List[str]:
    """사용자 안내 메시지에 넣을 표시용 데이터셋 이름을 반환한다."""

    return [get_dataset_label(key) for key in dataset_keys]
