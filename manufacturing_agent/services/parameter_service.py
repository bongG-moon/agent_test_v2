"""사용자 질문에서 조회 파라미터를 추출하는 서비스."""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..analysis.contracts import RequiredParams
from ..domain.knowledge import (
    DEN_GROUPS,
    INDIVIDUAL_PROCESSES,
    MODE_GROUPS,
    PKG_TYPE1_GROUPS,
    PKG_TYPE2_GROUPS,
    PROCESS_GROUPS,
    PROCESS_KEYWORD_RULES,
    PROCESS_SPECS,
    SPECIAL_PRODUCT_KEYWORD_RULES,
    TECH_GROUPS,
    build_domain_knowledge_prompt,
)
from ..domain.registry import (
    build_registered_domain_prompt,
    detect_registered_values,
    expand_registered_values,
)
from ..shared.config import SYSTEM_PROMPT, get_llm
from ..shared.filter_utils import normalize_text


OPER_NUM_PATTERNS = [
    r"(?:공정번호|oper_num|oper|operation)\s*[:=]?\s*(\d{4})",
    r"(\d{4})\s*번?\s*공정",
]

OPER_NUM_VALUES = [spec["OPER_NUM"] for spec in PROCESS_SPECS]


GROUP_FIELD_SPECS = [
    {
        "field_name": "process_name",
        "groups": PROCESS_GROUPS,
        "literal_values": INDIVIDUAL_PROCESSES + ["INPUT"],
    },
    {"field_name": "mode", "groups": MODE_GROUPS, "literal_values": None},
    {"field_name": "den", "groups": DEN_GROUPS, "literal_values": None},
    {"field_name": "tech", "groups": TECH_GROUPS, "literal_values": None},
    {"field_name": "pkg_type1", "groups": PKG_TYPE1_GROUPS, "literal_values": None},
    {"field_name": "pkg_type2", "groups": PKG_TYPE2_GROUPS, "literal_values": None},
]


def _get_llm_for_task(task: str):
    """환경 차이를 흡수하면서 LLM 객체를 안전하게 가져온다."""

    try:
        return get_llm(task=task)
    except TypeError:
        return get_llm()


def _extract_text_from_response(content: Any) -> str:
    """LLM 응답을 문자열 하나로 정리한다."""

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


def _parse_json_block(text: str) -> Dict[str, Any]:
    """코드 블록이 섞여 있어도 JSON 객체만 추출한다."""

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


def _merge_unique_values(*values: Any) -> List[str] | None:
    """단일 값, 리스트, None 을 모두 받아 순서를 유지한 고유 리스트로 합친다."""

    merged: List[str] = []
    for value in values:
        if value is None:
            continue
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            cleaned = str(candidate).strip()
            if cleaned and cleaned not in merged:
                merged.append(cleaned)
    return merged or None


def _contains_alias(text: str, alias: str) -> bool:
    """별칭이 다른 단어에 붙어 있는 오탐을 줄이기 위해 토큰 경계를 확인한다."""

    normalized_text = normalize_text(text)
    normalized_alias = normalize_text(alias)
    if not normalized_text or not normalized_alias:
        return False

    pattern = rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])"
    return bool(re.search(pattern, normalized_text, flags=re.IGNORECASE))


def _find_keyword_rule_targets(text: Any, keyword_rules: List[Dict[str, Any]]) -> List[str] | None:
    """도메인 키워드 규칙 목록을 보고 질문이나 값에서 목표 값을 찾는다."""

    matched_targets: List[str] = []
    for rule in keyword_rules:
        aliases = rule.get("aliases", [])
        if any(_contains_alias(str(text or ""), alias) for alias in aliases):
            matched_targets.append(str(rule.get("target_value", "")).strip())
    return _merge_unique_values(matched_targets)


def _canonicalize_group_values(
    raw_values: Any,
    groups: Dict[str, Dict[str, Any]],
    literal_values: List[str] | None = None,
) -> List[str] | None:
    """LLM이 뽑은 값이 그룹 이름이면 실제 값 목록으로 확장한다."""

    canonical_values: List[str] = []
    for raw_value in _merge_unique_values(raw_values) or []:
        matched = False

        for group in groups.values():
            aliases = [*group.get("synonyms", []), *group.get("actual_values", [])]
            if any(normalize_text(raw_value) == normalize_text(alias) for alias in aliases):
                canonical_values.extend(group.get("actual_values", []))
                matched = True
                break

        if matched:
            continue

        for literal_value in literal_values or []:
            if normalize_text(raw_value) == normalize_text(literal_value):
                canonical_values.append(literal_value)
                matched = True
                break

        if not matched:
            canonical_values.append(raw_value)

    return _merge_unique_values(canonical_values)


def _detect_group_values_from_text(
    text: str,
    groups: Dict[str, Dict[str, Any]],
    literal_values: List[str] | None = None,
) -> List[str] | None:
    """질문 전체를 보고 그룹 별칭이나 실제 값을 직접 탐지한다."""

    detected_values: List[str] = []

    for group in groups.values():
        aliases = [*group.get("synonyms", []), *group.get("actual_values", [])]
        if any(_contains_alias(text, alias) for alias in aliases):
            detected_values.extend(group.get("actual_values", []))

    for literal_value in literal_values or []:
        if _contains_alias(text, literal_value):
            detected_values.append(literal_value)

    return _merge_unique_values(detected_values)


def _detect_candidate_values(
    text: str,
    candidates: List[str] | None = None,
    patterns: List[str] | None = None,
) -> List[str] | None:
    """그룹이 아닌 코드형 값은 후보 목록과 정규식 패턴을 함께 사용해 탐지한다."""

    detected_values: List[str] = []

    for candidate in candidates or []:
        if _contains_alias(text, candidate):
            detected_values.append(candidate)

    for pattern in patterns or []:
        matches = re.findall(pattern, str(text or ""), flags=re.IGNORECASE)
        for match in matches:
            value = match if isinstance(match, str) else match[0]
            cleaned = str(value).strip()
            if cleaned:
                detected_values.append(cleaned)

    return _merge_unique_values(detected_values)


def _resolve_group_field(
    extracted_params: RequiredParams,
    user_input: str,
    field_name: str,
    groups: Dict[str, Dict[str, Any]],
    literal_values: List[str] | None = None,
) -> None:
    """그룹형 필드(process, mode, pkg 등)를 공통 규칙으로 보정한다."""

    current_value = _canonicalize_group_values(extracted_params.get(field_name), groups, literal_values=literal_values)
    current_value = _merge_unique_values(
        current_value,
        expand_registered_values(field_name, current_value),
    )

    if not current_value:
        current_value = _detect_group_values_from_text(user_input, groups, literal_values=literal_values)

    extracted_params[field_name] = _merge_unique_values(
        current_value,
        detect_registered_values(field_name, user_input),
    )


def _resolve_oper_num_field(extracted_params: RequiredParams, user_input: str) -> None:
    """OPER_NUM 은 도메인 값 목록과 패턴을 함께 사용해 탐지한다."""

    current_value = _merge_unique_values(
        extracted_params.get("oper_num"),
        expand_registered_values("oper_num", extracted_params.get("oper_num")),
    )

    if not current_value:
        current_value = _detect_candidate_values(
            user_input,
            candidates=OPER_NUM_VALUES,
            patterns=OPER_NUM_PATTERNS,
        )

    extracted_params["oper_num"] = _merge_unique_values(
        current_value,
        detect_registered_values("oper_num", user_input),
    )


def _resolve_scalar_registered_field(
    extracted_params: RequiredParams,
    user_input: str,
    field_name: str,
) -> None:
    """단일 값 필드는 등록 규칙 기반으로 하나의 대표 값을 고른다."""

    expanded_value = expand_registered_values(field_name, extracted_params.get(field_name))
    if expanded_value:
        extracted_params[field_name] = expanded_value[0]
        return

    if extracted_params.get(field_name):
        return

    detected_value = detect_registered_values(field_name, user_input)
    if detected_value:
        extracted_params[field_name] = detected_value[0]


def _resolve_keyword_based_scalar_field(
    extracted_params: RequiredParams,
    user_input: str,
    field_name: str,
    keyword_rules: List[Dict[str, Any]],
) -> None:
    """도메인 키워드 규칙으로 단일 값 필드를 정규화한다."""

    normalized_value = _find_keyword_rule_targets(extracted_params.get(field_name), keyword_rules)
    if normalized_value:
        extracted_params[field_name] = normalized_value[0]
        return

    if extracted_params.get(field_name):
        return

    detected_value = _find_keyword_rule_targets(user_input, keyword_rules)
    if detected_value:
        extracted_params[field_name] = detected_value[0]


def _resolve_keyword_based_process_field(
    extracted_params: RequiredParams,
    user_input: str,
    keyword_rules: List[Dict[str, Any]],
) -> None:
    """질문 키워드를 공정 값으로 바꾸는 규칙을 적용한다."""

    detected_processes = _find_keyword_rule_targets(user_input, keyword_rules)
    if not extracted_params.get("process_name") and detected_processes:
        extracted_params["process_name"] = detected_processes
        return

    if extracted_params.get("process_name") == ["INPUT"] and not detected_processes:
        extracted_params["process_name"] = None


def _inherit_from_context(extracted_params: RequiredParams, context: Dict[str, Any] | None) -> RequiredParams:
    """이번 질문에서 비어 있는 조건은 직전 문맥에서 이어받는다."""

    if not isinstance(context, dict):
        return extracted_params

    if not extracted_params.get("date") and context.get("date"):
        extracted_params["date"] = context["date"]
        extracted_params["date_inherited"] = True

    for field in [
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
    ]:
        if extracted_params.get(field) or not context.get(field):
            continue

        extracted_params[field] = context[field]
        inherited_key = (
            "process_inherited"
            if field == "process_name"
            else "oper_num_inherited"
            if field == "oper_num"
            else "pkg_type1_inherited"
            if field == "pkg_type1"
            else "pkg_type2_inherited"
            if field == "pkg_type2"
            else "product_inherited"
            if field == "product_name"
            else "line_inherited"
            if field == "line_name"
            else f"{field}_inherited"
        )
        extracted_params[inherited_key] = True

    return extracted_params


def _fallback_date(text: str) -> str | None:
    """LLM이 날짜를 놓쳤을 때 오늘, 어제 같은 기본 표현을 보정한다."""

    lower = str(text or "").lower()
    now = datetime.now()
    if "오늘" in lower or "today" in lower:
        return now.strftime("%Y%m%d")
    if "어제" in lower or "yesterday" in lower:
        return (now - timedelta(days=1)).strftime("%Y%m%d")
    return None


def _apply_domain_overrides(extracted_params: RequiredParams, user_input: str) -> RequiredParams:
    """LLM 초안에 도메인 규칙과 사용자 정의 규칙을 덧입혀 최종 필터로 정리한다."""

    _resolve_keyword_based_process_field(extracted_params, user_input, PROCESS_KEYWORD_RULES)
    _resolve_keyword_based_scalar_field(
        extracted_params,
        user_input,
        field_name="product_name",
        keyword_rules=SPECIAL_PRODUCT_KEYWORD_RULES,
    )

    for spec in GROUP_FIELD_SPECS:
        _resolve_group_field(
            extracted_params,
            user_input,
            field_name=spec["field_name"],
            groups=spec["groups"],
            literal_values=spec["literal_values"],
        )

    _resolve_oper_num_field(extracted_params, user_input)

    _resolve_scalar_registered_field(extracted_params, user_input, "product_name")
    _resolve_scalar_registered_field(extracted_params, user_input, "line_name")
    _resolve_scalar_registered_field(extracted_params, user_input, "mcp_no")

    return extracted_params


def resolve_required_params(
    user_input: str,
    chat_history_text: str,
    current_data_columns: List[str],
    context: Dict[str, Any] | None = None,
) -> RequiredParams:
    """질문에서 조회에 필요한 파라미터를 추출해 반환한다.

    처리 순서는 아래와 같다.
    1. LLM에게 JSON 형태의 초안 파라미터를 요청한다.
    2. 날짜 같은 기본 규칙을 보정한다.
    3. 도메인 그룹, 등록 규칙, 특수 제품 규칙으로 값을 보정한다.
    4. 비어 있는 값은 이전 문맥에서 이어받는다.
    """

    today = datetime.now().strftime("%Y%m%d")
    domain_prompt = build_domain_knowledge_prompt()
    custom_domain_prompt = build_registered_domain_prompt()
    prompt = f"""You are extracting retrieval parameters for a manufacturing data assistant.
Return JSON only.

Rules:
- Extract only retrieval-safe fields and grouping hints.
- Normalize today/yesterday into YYYYMMDD.
- Use domain knowledge to expand process groups.
- If a value is not explicit, return null.

Domain knowledge:
{domain_prompt}

Custom domain registry:
{custom_domain_prompt}

Recent chat:
{chat_history_text}

Available current-data columns:
{", ".join(current_data_columns) if current_data_columns else "(none)"}

Today's date:
{today}

User question:
{user_input}

Return only:
{{
  "date": "YYYYMMDD or null",
  "process": ["value"] or null,
  "oper_num": ["value"] or null,
  "pkg_type1": ["value"] or null,
  "pkg_type2": ["value"] or null,
  "product_name": "string or null",
  "line_name": "string or null",
  "mode": ["value"] or null,
  "den": ["value"] or null,
  "tech": ["value"] or null,
  "lead": "string or null",
  "mcp_no": "string or null",
  "group_by": "column or null"
}}"""

    parsed: Dict[str, Any] = {}
    try:
        llm = _get_llm_for_task("parameter_extract")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        parsed = _parse_json_block(_extract_text_from_response(response.content))
    except Exception:
        parsed = {}

    extracted_params: RequiredParams = {
        "date": parsed.get("date") or _fallback_date(user_input),
        "process_name": parsed.get("process"),
        "oper_num": parsed.get("oper_num"),
        "pkg_type1": parsed.get("pkg_type1"),
        "pkg_type2": parsed.get("pkg_type2"),
        "product_name": parsed.get("product_name"),
        "line_name": parsed.get("line_name"),
        "group_by": parsed.get("group_by"),
        "metrics": [],
        "mode": parsed.get("mode"),
        "den": parsed.get("den"),
        "tech": parsed.get("tech"),
        "lead": parsed.get("lead"),
        "mcp_no": parsed.get("mcp_no"),
    }
    extracted_params = _apply_domain_overrides(extracted_params, user_input)
    return _inherit_from_context(extracted_params, context)
