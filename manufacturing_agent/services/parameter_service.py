import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..analysis.contracts import RequiredParams
from ..shared.config import SYSTEM_PROMPT, get_llm
from ..domain.knowledge import (
    DEN_GROUPS,
    INDIVIDUAL_PROCESSES,
    MODE_GROUPS,
    PKG_TYPE1_GROUPS,
    PKG_TYPE2_GROUPS,
    PROCESS_GROUPS,
    TECH_GROUPS,
    build_domain_knowledge_prompt,
)
from ..domain.registry import (
    build_registered_domain_prompt,
    detect_registered_values,
    expand_registered_values,
)
from ..shared.filter_utils import normalize_text


def _get_llm_for_task(task: str):
    try:
        return get_llm(task=task)
    except TypeError:
        return get_llm()


def _extract_text_from_response(content: Any) -> str:
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


def _inherit_from_context(extracted_params: RequiredParams, context: Dict[str, Any] | None) -> RequiredParams:
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
        if extracted_params.get(field):
            continue
        if not context.get(field):
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
    lower = str(text or "").lower()
    now = datetime.now()
    if "?ㅻ뒛" in lower or "today" in lower:
        return now.strftime("%Y%m%d")
    if "?댁젣" in lower or "yesterday" in lower:
        return (now - timedelta(days=1)).strftime("%Y%m%d")
    return None


def _detect_oper_num(text: str) -> List[str] | None:
    patterns = [
        r"(?:怨듭젙踰덊샇|oper_num|oper|operation)\s*[:=]?\s*(\d{4})",
        r"(\d{4})\s*踰?\s*怨듭젙",
    ]
    values: List[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, str(text or ""), flags=re.IGNORECASE):
            if match not in values:
                values.append(match)
    return values or None


def _detect_pkg_values(text: str, allowed_values: List[str]) -> List[str] | None:
    normalized = normalize_text(text)
    detected: List[str] = []
    for value in allowed_values:
        if normalize_text(value) in normalized and value not in detected:
            detected.append(value)
    return detected or None


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _dedupe(values: List[str]) -> List[str]:
    ordered: List[str] = []
    for value in values:
        if value and value not in ordered:
            ordered.append(value)
    return ordered


def _merge_optional_lists(current_value: Any, extra_value: Any) -> List[str] | None:
    merged = _dedupe([*_as_list(current_value), *_as_list(extra_value)])
    return merged or None


def _contains_alias(text: str, alias: str) -> bool:
    normalized_text = normalize_text(text)
    normalized_alias = normalize_text(alias)
    if not normalized_text or not normalized_alias:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])"
    return bool(re.search(pattern, normalized_text, flags=re.IGNORECASE))


def _canonicalize_group_values(
    raw_values: Any,
    groups: Dict[str, Dict[str, Any]],
    literal_values: List[str] | None = None,
) -> List[str] | None:
    canonical_values: List[str] = []

    for raw_value in _as_list(raw_values):
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

    canonical_values = _dedupe(canonical_values)
    return canonical_values or None


def _detect_group_values_from_text(
    text: str,
    groups: Dict[str, Dict[str, Any]],
    literal_values: List[str] | None = None,
) -> List[str] | None:
    detected_values: List[str] = []

    for group in groups.values():
        aliases = [*group.get("synonyms", []), *group.get("actual_values", [])]
        if any(_contains_alias(text, alias) for alias in aliases):
            detected_values.extend(group.get("actual_values", []))

    for literal_value in literal_values or []:
        if _contains_alias(text, literal_value):
            detected_values.append(literal_value)

    detected_values = _dedupe(detected_values)
    return detected_values or None


def _normalize_special_product_name(value: Any) -> str | None:
    normalized = normalize_text(value)
    if not normalized:
        return None

    hbm_or_3ds_tokens = [
        "hbm_or_3ds",
        "hbm/3ds",
        "hbm",
        "3ds",
        "hbm?쒗뭹",
        "hbm?먯옱",
        "3ds?쒗뭹",
    ]
    auto_tokens = ["auto_product", "auto", "automotive", "차량", "오토"]

    if any(token in normalized for token in hbm_or_3ds_tokens):
        return "HBM_OR_3DS"
    if any(token in normalized for token in auto_tokens):
        return "AUTO_PRODUCT"
    return None


def _apply_domain_overrides(extracted_params: RequiredParams, user_input: str) -> RequiredParams:
    normalized = normalize_text(user_input)
    input_requested = any(token in normalized for token in ["?ъ엯??", "input", "?명뭼"])

    if not extracted_params.get("process_name") and input_requested:
        extracted_params["process_name"] = ["INPUT"]

    normalized_product_name = _normalize_special_product_name(extracted_params.get("product_name"))
    if normalized_product_name:
        extracted_params["product_name"] = normalized_product_name
    elif not extracted_params.get("product_name"):
        requested_special_product = _normalize_special_product_name(user_input)
        if requested_special_product:
            extracted_params["product_name"] = requested_special_product

    if extracted_params.get("process_name") == ["INPUT"] and not input_requested:
        extracted_params["process_name"] = None

    extracted_params["process_name"] = _canonicalize_group_values(
        extracted_params.get("process_name"),
        PROCESS_GROUPS,
        literal_values=INDIVIDUAL_PROCESSES + ["INPUT"],
    )
    extracted_params["process_name"] = _merge_optional_lists(
        extracted_params.get("process_name"),
        expand_registered_values("process_name", extracted_params.get("process_name")),
    )
    if not extracted_params.get("process_name"):
        detected_processes = _detect_group_values_from_text(
            user_input,
            PROCESS_GROUPS,
            literal_values=INDIVIDUAL_PROCESSES + ["INPUT"],
        )
        if detected_processes:
            extracted_params["process_name"] = detected_processes
    extracted_params["process_name"] = _merge_optional_lists(
        extracted_params.get("process_name"),
        detect_registered_values("process_name", user_input),
    )

    if not extracted_params.get("oper_num"):
        detected_oper_num = _detect_oper_num(user_input)
        if detected_oper_num:
            extracted_params["oper_num"] = detected_oper_num
    extracted_params["oper_num"] = _merge_optional_lists(
        extracted_params.get("oper_num"),
        detect_registered_values("oper_num", user_input),
    )

    extracted_params["mode"] = _canonicalize_group_values(extracted_params.get("mode"), MODE_GROUPS)
    extracted_params["mode"] = _merge_optional_lists(
        extracted_params.get("mode"),
        expand_registered_values("mode", extracted_params.get("mode")),
    )
    if not extracted_params.get("mode"):
        detected_mode = _detect_group_values_from_text(user_input, MODE_GROUPS)
        if detected_mode:
            extracted_params["mode"] = detected_mode
    extracted_params["mode"] = _merge_optional_lists(
        extracted_params.get("mode"),
        detect_registered_values("mode", user_input),
    )

    extracted_params["den"] = _canonicalize_group_values(extracted_params.get("den"), DEN_GROUPS)
    extracted_params["den"] = _merge_optional_lists(
        extracted_params.get("den"),
        expand_registered_values("den", extracted_params.get("den")),
    )
    if not extracted_params.get("den"):
        detected_den = _detect_group_values_from_text(user_input, DEN_GROUPS)
        if detected_den:
            extracted_params["den"] = detected_den
    extracted_params["den"] = _merge_optional_lists(
        extracted_params.get("den"),
        detect_registered_values("den", user_input),
    )

    extracted_params["tech"] = _canonicalize_group_values(extracted_params.get("tech"), TECH_GROUPS)
    extracted_params["tech"] = _merge_optional_lists(
        extracted_params.get("tech"),
        expand_registered_values("tech", extracted_params.get("tech")),
    )
    if not extracted_params.get("tech"):
        detected_tech = _detect_group_values_from_text(user_input, TECH_GROUPS)
        if detected_tech:
            extracted_params["tech"] = detected_tech
    extracted_params["tech"] = _merge_optional_lists(
        extracted_params.get("tech"),
        detect_registered_values("tech", user_input),
    )

    extracted_params["pkg_type1"] = _canonicalize_group_values(extracted_params.get("pkg_type1"), PKG_TYPE1_GROUPS)
    extracted_params["pkg_type1"] = _merge_optional_lists(
        extracted_params.get("pkg_type1"),
        expand_registered_values("pkg_type1", extracted_params.get("pkg_type1")),
    )
    if not extracted_params.get("pkg_type1"):
        detected_pkg_type1 = _detect_pkg_values(user_input, ["FCBGA", "LFBGA"])
        if detected_pkg_type1:
            extracted_params["pkg_type1"] = detected_pkg_type1
    extracted_params["pkg_type1"] = _merge_optional_lists(
        extracted_params.get("pkg_type1"),
        detect_registered_values("pkg_type1", user_input),
    )

    extracted_params["pkg_type2"] = _canonicalize_group_values(extracted_params.get("pkg_type2"), PKG_TYPE2_GROUPS)
    extracted_params["pkg_type2"] = _merge_optional_lists(
        extracted_params.get("pkg_type2"),
        expand_registered_values("pkg_type2", extracted_params.get("pkg_type2")),
    )
    if not extracted_params.get("pkg_type2"):
        detected_pkg_type2 = _detect_pkg_values(user_input, ["ODP", "16DP", "SDP"])
        if detected_pkg_type2:
            extracted_params["pkg_type2"] = detected_pkg_type2
    extracted_params["pkg_type2"] = _merge_optional_lists(
        extracted_params.get("pkg_type2"),
        detect_registered_values("pkg_type2", user_input),
    )

    extracted_params["product_name"] = (
        _normalize_special_product_name(extracted_params.get("product_name"))
        or extracted_params.get("product_name")
    )
    expanded_product = expand_registered_values("product_name", extracted_params.get("product_name"))
    if expanded_product:
        extracted_params["product_name"] = expanded_product[0]
    if not extracted_params.get("product_name"):
        detected_product = detect_registered_values("product_name", user_input)
        if detected_product:
            extracted_params["product_name"] = detected_product[0]

    expanded_line = expand_registered_values("line_name", extracted_params.get("line_name"))
    if expanded_line:
        extracted_params["line_name"] = expanded_line[0]
    if not extracted_params.get("line_name"):
        detected_line = detect_registered_values("line_name", user_input)
        if detected_line:
            extracted_params["line_name"] = detected_line[0]

    expanded_mcp = expand_registered_values("mcp_no", extracted_params.get("mcp_no"))
    if expanded_mcp:
        extracted_params["mcp_no"] = expanded_mcp[0]
    if not extracted_params.get("mcp_no"):
        detected_mcp = detect_registered_values("mcp_no", user_input)
        if detected_mcp:
            extracted_params["mcp_no"] = detected_mcp[0]

    return extracted_params


def resolve_required_params(
    user_input: str,
    chat_history_text: str,
    current_data_columns: List[str],
    context: Dict[str, Any] | None = None,
) -> RequiredParams:
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

