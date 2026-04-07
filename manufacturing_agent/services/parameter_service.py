"""사용자 질문에서 조회 파라미터를 추출하는 서비스."""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..analysis.contracts import RequiredParams
from ..domain.knowledge import PARAMETER_FIELD_SPECS, build_domain_knowledge_prompt
from ..domain.registry import build_registered_domain_prompt, detect_registered_values, expand_registered_values
from ..shared.config import SYSTEM_PROMPT, get_llm
from ..shared.filter_utils import normalize_text


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


def _match_keyword_rules(text: Any, keyword_rules: List[Dict[str, Any]] | None) -> List[str] | None:
    """도메인 키워드 규칙에서 목표 값을 찾는다."""

    matched_targets: List[str] = []
    for rule in keyword_rules or []:
        aliases = rule.get("aliases", [])
        if any(_contains_alias(str(text or ""), alias) for alias in aliases):
            matched_targets.append(str(rule.get("target_value", "")).strip())
    return _merge_unique_values(matched_targets)


def _expand_group_values(
    raw_values: Any,
    groups: Dict[str, Dict[str, Any]] | None,
    literal_values: List[str] | None = None,
) -> List[str] | None:
    """LLM이 뽑아낸 그룹형 값을 실제 조회 값 목록으로 확장한다."""

    if not groups:
        return _merge_unique_values(raw_values)

    expanded_values: List[str] = []
    for raw_value in _merge_unique_values(raw_values) or []:
        matched = False
        for group in groups.values():
            aliases = [*group.get("synonyms", []), *group.get("actual_values", [])]
            if any(normalize_text(raw_value) == normalize_text(alias) for alias in aliases):
                expanded_values.extend(group.get("actual_values", []))
                matched = True
                break

        if matched:
            continue

        for literal_value in literal_values or []:
            if normalize_text(raw_value) == normalize_text(literal_value):
                expanded_values.append(literal_value)
                matched = True
                break

        if not matched:
            expanded_values.append(raw_value)

    return _merge_unique_values(expanded_values)


def _detect_group_values_from_text(
    text: str,
    groups: Dict[str, Dict[str, Any]] | None,
    literal_values: List[str] | None = None,
) -> List[str] | None:
    """질문 원문에서 그룹형 값을 직접 찾는다."""

    if not groups:
        return None

    detected_values: List[str] = []
    for group in groups.values():
        aliases = [*group.get("synonyms", []), *group.get("actual_values", [])]
        if any(_contains_alias(text, alias) for alias in aliases):
            detected_values.extend(group.get("actual_values", []))

    for literal_value in literal_values or []:
        if _contains_alias(text, literal_value):
            detected_values.append(literal_value)

    return _merge_unique_values(detected_values)


def _detect_candidate_values_from_text(
    text: str,
    candidate_values: List[str] | None = None,
    patterns: List[str] | None = None,
) -> List[str] | None:
    """코드형 값은 후보 목록과 패턴을 사용해 원문에서 찾는다."""

    detected_values: List[str] = []

    for candidate in candidate_values or []:
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


def _normalize_single_value(field_name: str, value: Any, user_input: str) -> str | None:
    """단일 값 필드는 등록 규칙과 텍스트 탐지를 거쳐 하나의 값으로 정리한다."""

    expanded_value = expand_registered_values(field_name, value)
    if expanded_value:
        return expanded_value[0]

    if value:
        cleaned = str(value).strip()
        return cleaned or None

    detected_value = detect_registered_values(field_name, user_input)
    return detected_value[0] if detected_value else None


def _normalize_multi_value(field_name: str, value: Any, user_input: str, field_spec: Dict[str, Any]) -> List[str] | None:
    """리스트형 필드는 LLM 추출값을 우선하고, 없을 때만 텍스트 기반 탐지를 사용한다."""

    normalized_value = _match_keyword_rules(value, field_spec.get("keyword_rules"))
    normalized_value = _merge_unique_values(normalized_value, value)
    normalized_value = _expand_group_values(
        normalized_value,
        field_spec.get("groups"),
        literal_values=field_spec.get("literal_values"),
    )
    normalized_value = _merge_unique_values(
        normalized_value,
        expand_registered_values(field_name, normalized_value),
    )

    if not normalized_value and field_spec.get("allow_text_detection"):
        normalized_value = _match_keyword_rules(user_input, field_spec.get("keyword_rules"))
        normalized_value = _merge_unique_values(
            normalized_value,
            _detect_group_values_from_text(
                user_input,
                field_spec.get("groups"),
                literal_values=field_spec.get("literal_values"),
            ),
            _detect_candidate_values_from_text(
                user_input,
                candidate_values=field_spec.get("candidate_values"),
                patterns=field_spec.get("patterns"),
            ),
        )

    normalized_value = _merge_unique_values(
        normalized_value,
        detect_registered_values(field_name, user_input),
    )
    return normalized_value


def _normalize_field_value(field_spec: Dict[str, Any], extracted_params: RequiredParams, user_input: str) -> None:
    """도메인 스펙 하나를 기준으로 필드 값을 정규화한다."""

    field_name = field_spec["field_name"]
    current_value = extracted_params.get(field_name)

    if field_spec.get("value_kind") == "single":
        keyword_value = _match_keyword_rules(current_value, field_spec.get("keyword_rules"))
        if not keyword_value and field_spec.get("allow_text_detection"):
            keyword_value = _match_keyword_rules(user_input, field_spec.get("keyword_rules"))
        extracted_params[field_name] = _normalize_single_value(
            field_name,
            keyword_value[0] if keyword_value else current_value,
            user_input,
        )
        return

    extracted_params[field_name] = _normalize_multi_value(field_name, current_value, user_input, field_spec)


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


def _build_initial_params(parsed: Dict[str, Any], user_input: str) -> RequiredParams:
    """LLM JSON 응답을 내부 파라미터 구조로 옮긴다."""

    extracted_params: RequiredParams = {
        "date": parsed.get("date") or _fallback_date(user_input),
        "group_by": parsed.get("group_by"),
        "metrics": [],
        "lead": parsed.get("lead"),
    }

    for field_spec in PARAMETER_FIELD_SPECS:
        extracted_params[field_spec["field_name"]] = parsed.get(field_spec["response_key"])

    return extracted_params


def _apply_domain_specs(extracted_params: RequiredParams, user_input: str) -> RequiredParams:
    """필드별 하드코딩 함수 대신 도메인 스펙 목록을 돌며 공통 처리한다."""

    for field_spec in PARAMETER_FIELD_SPECS:
        _normalize_field_value(field_spec, extracted_params, user_input)
    return extracted_params


def resolve_required_params(
    user_input: str,
    chat_history_text: str,
    current_data_columns: List[str],
    context: Dict[str, Any] | None = None,
) -> RequiredParams:
    """질문에서 조회에 필요한 파라미터를 추출해 반환한다.

    처리 순서는 아래와 같다.
    1. LLM이 질문과 도메인 텍스트를 보고 JSON 초안을 만든다.
    2. 코드는 도메인 스펙을 읽어 값을 정규화한다.
    3. 비어 있는 값은 이전 문맥에서 이어받는다.
    """

    today = datetime.now().strftime("%Y%m%d")
    domain_prompt = build_domain_knowledge_prompt()
    custom_domain_prompt = build_registered_domain_prompt()
    prompt = f"""You are extracting retrieval parameters for a manufacturing data assistant.
Return JSON only.

Rules:
- Extract only retrieval-safe fields and grouping hints.
- Normalize today/yesterday into YYYYMMDD.
- Use domain knowledge to expand process groups and interpret aliases.
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

    extracted_params = _build_initial_params(parsed, user_input)
    extracted_params = _apply_domain_specs(extracted_params, user_input)
    return _inherit_from_context(extracted_params, context)
