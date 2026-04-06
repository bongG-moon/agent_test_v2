from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..shared.config import SYSTEM_PROMPT, get_llm
from ..shared.filter_utils import normalize_text
from .knowledge import (
    DATASET_METADATA,
    DEN_GROUPS,
    MODE_GROUPS,
    PKG_TYPE1_GROUPS,
    PKG_TYPE2_GROUPS,
    PROCESS_GROUPS,
    SPECIAL_PRODUCT_ALIASES,
    TECH_GROUPS,
)


def _get_llm_for_task(task: str):
    try:
        return get_llm(task=task)
    except TypeError:
        return get_llm()


ROOT_DIR = Path(__file__).resolve().parents[2]
DOMAIN_REGISTRY_DIR = ROOT_DIR / "reference_materials" / "domain_registry"
DOMAIN_REGISTRY_ENTRIES_DIR = DOMAIN_REGISTRY_DIR / "entries"

SUPPORTED_VALUE_FIELDS = {
    "process_name",
    "mode",
    "den",
    "tech",
    "pkg_type1",
    "pkg_type2",
    "product_name",
    "line_name",
    "oper_num",
    "mcp_no",
}

FIELD_NAME_ALIASES = {
    "process": "process_name",
    "process_name": "process_name",
    "oper_name": "process_name",
    "mode": "mode",
    "den": "den",
    "density": "den",
    "tech": "tech",
    "pkg1": "pkg_type1",
    "pkg_type1": "pkg_type1",
    "pkg2": "pkg_type2",
    "pkg_type2": "pkg_type2",
    "product": "product_name",
    "product_name": "product_name",
    "line": "line_name",
    "line_name": "line_name",
    "oper_num": "oper_num",
    "mcp": "mcp_no",
    "mcp_no": "mcp_no",
}

VALID_CALCULATION_MODES = {
    "",
    "ratio",
    "difference",
    "sum",
    "mean",
    "count",
    "condition_flag",
    "threshold_flag",
    "count_if",
    "sum_if",
    "mean_if",
    "custom",
}

VALID_JOIN_TYPES = {"left", "inner", "right", "outer"}

DEFAULT_ANALYSIS_RULES = [
    {
        "name": "achievement_rate",
        "display_name": "achievement rate",
        "synonyms": ["achievement rate", "달성률", "목표 대비 생산"],
        "required_datasets": ["production", "target"],
        "required_columns": ["production", "target"],
        "source_columns": [
            {"dataset_key": "production", "column": "production", "role": "numerator"},
            {"dataset_key": "target", "column": "target", "role": "denominator"},
        ],
        "calculation_mode": "ratio",
        "output_column": "achievement_rate",
        "default_group_by": ["OPER_NAME"],
        "condition": "",
        "decision_rule": "",
        "formula": "production / target",
        "pandas_hint": "group by OPER_NAME and calculate production / target",
        "description": "Calculate production achievement rate using production and target.",
        "source": "builtin",
    },
    {
        "name": "yield_rate",
        "display_name": "yield rate",
        "synonyms": ["yield", "yield rate", "수율"],
        "required_datasets": ["yield"],
        "required_columns": ["yield_rate", "pass_qty", "tested_qty"],
        "source_columns": [
            {"dataset_key": "yield", "column": "yield_rate", "role": "preferred_metric"},
            {"dataset_key": "yield", "column": "pass_qty", "role": "pass_qty"},
            {"dataset_key": "yield", "column": "tested_qty", "role": "tested_qty"},
        ],
        "calculation_mode": "ratio",
        "output_column": "yield_rate",
        "default_group_by": ["OPER_NAME"],
        "condition": "",
        "decision_rule": "",
        "formula": "yield_rate or pass_qty / tested_qty",
        "pandas_hint": "group by OPER_NAME and average yield_rate",
        "description": "Analyze yield-focused questions with yield data.",
        "source": "builtin",
    },
]

DEFAULT_JOIN_RULES: List[Dict[str, Any]] = []


def _ensure_registry_dirs() -> None:
    DOMAIN_REGISTRY_ENTRIES_DIR.mkdir(parents=True, exist_ok=True)


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


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _dedupe(values: Iterable[str]) -> List[str]:
    ordered: List[str] = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in ordered:
            ordered.append(cleaned)
    return ordered


def _normalize_field_name(value: Any) -> str:
    return FIELD_NAME_ALIASES.get(normalize_text(value), normalize_text(value))


def _normalize_value_group(raw_group: Dict[str, Any]) -> Dict[str, Any]:
    field_name = _normalize_field_name(raw_group.get("field"))
    canonical = str(raw_group.get("canonical", "")).strip()
    synonyms = _dedupe([canonical, *_as_list(raw_group.get("synonyms"))])
    values = _dedupe(_as_list(raw_group.get("values")))
    return {
        "field": field_name,
        "canonical": canonical,
        "synonyms": synonyms,
        "values": values,
        "description": str(raw_group.get("description", "")).strip(),
    }


def _normalize_dataset_keyword_rule(raw_rule: Dict[str, Any]) -> Dict[str, Any]:
    dataset_key = normalize_text(raw_rule.get("dataset_key"))
    keywords = _dedupe(_as_list(raw_rule.get("keywords")))
    return {"dataset_key": dataset_key, "keywords": keywords}


def _normalize_source_columns(raw_columns: Any) -> List[Dict[str, str]]:
    normalized_columns: List[Dict[str, str]] = []
    for item in raw_columns or []:
        if not isinstance(item, dict):
            continue
        dataset_key = normalize_text(item.get("dataset_key"))
        column = str(item.get("column", "")).strip()
        role = str(item.get("role", "")).strip()
        if dataset_key and column:
            normalized_columns.append({"dataset_key": dataset_key, "column": column, "role": role})
    return normalized_columns


def _normalize_analysis_rule(raw_rule: Dict[str, Any]) -> Dict[str, Any]:
    name = str(raw_rule.get("name", "")).strip()
    display_name = str(raw_rule.get("display_name", name)).strip() or name
    synonyms = _dedupe([name, display_name, *_as_list(raw_rule.get("synonyms"))])
    required_datasets = [normalize_text(item) for item in _as_list(raw_rule.get("required_datasets"))]
    required_columns = _dedupe(_as_list(raw_rule.get("required_columns")))
    source_columns = _normalize_source_columns(raw_rule.get("source_columns"))
    calculation_mode = str(raw_rule.get("calculation_mode", "")).strip()
    if calculation_mode not in VALID_CALCULATION_MODES:
        calculation_mode = "custom" if calculation_mode else ""
    return {
        "name": name,
        "display_name": display_name,
        "synonyms": synonyms,
        "required_datasets": required_datasets,
        "required_columns": required_columns,
        "source_columns": source_columns,
        "calculation_mode": calculation_mode,
        "output_column": str(raw_rule.get("output_column", "")).strip(),
        "default_group_by": _dedupe(_as_list(raw_rule.get("default_group_by"))),
        "condition": str(raw_rule.get("condition", "")).strip(),
        "decision_rule": str(raw_rule.get("decision_rule", "")).strip(),
        "formula": str(raw_rule.get("formula", "")).strip(),
        "pandas_hint": str(raw_rule.get("pandas_hint", "")).strip(),
        "description": str(raw_rule.get("description", "")).strip(),
        "source": str(raw_rule.get("source", "custom")).strip() or "custom",
    }


def _normalize_join_rule(raw_rule: Dict[str, Any]) -> Dict[str, Any]:
    join_type = str(raw_rule.get("join_type", "left")).strip().lower()
    if join_type not in VALID_JOIN_TYPES:
        join_type = "left"
    return {
        "name": str(raw_rule.get("name", "")).strip(),
        "base_dataset": normalize_text(raw_rule.get("base_dataset")),
        "join_dataset": normalize_text(raw_rule.get("join_dataset")),
        "join_type": join_type,
        "join_keys": _dedupe(_as_list(raw_rule.get("join_keys"))),
        "description": str(raw_rule.get("description", "")).strip(),
        "source": str(raw_rule.get("source", "custom")).strip() or "custom",
    }


def _normalize_entry_payload(payload: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    return {
        "id": str(payload.get("id", "")).strip() or datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "title": str(payload.get("title", "")).strip() or raw_text[:30].strip() or "domain note",
        "created_at": str(payload.get("created_at", "")).strip() or datetime.now().isoformat(),
        "raw_text": str(payload.get("raw_text", "")).strip() or raw_text,
        "dataset_keywords": [
            _normalize_dataset_keyword_rule(item)
            for item in payload.get("dataset_keywords", [])
            if isinstance(item, dict)
        ],
        "value_groups": [_normalize_value_group(item) for item in payload.get("value_groups", []) if isinstance(item, dict)],
        "analysis_rules": [_normalize_analysis_rule(item) for item in payload.get("analysis_rules", []) if isinstance(item, dict)],
        "join_rules": [_normalize_join_rule(item) for item in payload.get("join_rules", []) if isinstance(item, dict)],
        "notes": _dedupe(_as_list(payload.get("notes"))),
    }


def _build_builtin_value_groups() -> Dict[str, List[Dict[str, Any]]]:
    registry: Dict[str, List[Dict[str, Any]]] = {field: [] for field in SUPPORTED_VALUE_FIELDS}

    def add_group(field: str, canonical: str, synonyms: List[str], values: List[str], description: str) -> None:
        registry[field].append(
            {
                "field": field,
                "canonical": canonical,
                "synonyms": _dedupe([canonical, *synonyms]),
                "values": _dedupe(values),
                "description": description,
                "source": "builtin",
            }
        )

    for key, group in PROCESS_GROUPS.items():
        add_group("process_name", group.get("group_name", key), group.get("synonyms", []), group.get("actual_values", []), group.get("description", ""))
    for key, group in MODE_GROUPS.items():
        add_group("mode", key, group.get("synonyms", []), group.get("actual_values", []), group.get("description", ""))
    for key, group in DEN_GROUPS.items():
        add_group("den", key, group.get("synonyms", []), group.get("actual_values", []), group.get("description", ""))
    for key, group in TECH_GROUPS.items():
        add_group("tech", key, group.get("synonyms", []), group.get("actual_values", []), group.get("description", ""))
    for key, group in PKG_TYPE1_GROUPS.items():
        add_group("pkg_type1", key, group.get("synonyms", []), group.get("actual_values", []), group.get("description", ""))
    for key, group in PKG_TYPE2_GROUPS.items():
        add_group("pkg_type2", key, group.get("synonyms", []), group.get("actual_values", []), group.get("description", ""))

    registry["product_name"].append(
        {
            "field": "product_name",
            "canonical": "HBM_OR_3DS",
            "synonyms": ["HBM_OR_3DS", "HBM/3DS", *SPECIAL_PRODUCT_ALIASES["HBM_OR_3DS"]],
            "values": ["HBM_OR_3DS"],
            "description": "TSV-based products such as HBM and 3DS.",
            "source": "builtin",
        }
    )
    registry["product_name"].append(
        {
            "field": "product_name",
            "canonical": "AUTO_PRODUCT",
            "synonyms": ["AUTO_PRODUCT", "AUTO", *SPECIAL_PRODUCT_ALIASES["AUTO_PRODUCT"]],
            "values": ["AUTO_PRODUCT"],
            "description": "Automotive products.",
            "source": "builtin",
        }
    )
    return registry


def _build_builtin_dataset_keywords() -> Dict[str, List[str]]:
    return {key: list(meta.get("keywords", [])) for key, meta in DATASET_METADATA.items()}


def _keyword_owners(registry: Dict[str, Any]) -> Dict[str, str]:
    owners: Dict[str, str] = {}
    for dataset_key, keywords in _build_builtin_dataset_keywords().items():
        for keyword in keywords:
            owners[normalize_text(keyword)] = dataset_key
    for rule in registry.get("dataset_keywords", []):
        dataset_key = rule["dataset_key"]
        for keyword in rule["keywords"]:
            owners[normalize_text(keyword)] = dataset_key
    return owners


def load_domain_registry() -> Dict[str, Any]:
    _ensure_registry_dirs()
    registry = {
        "entries": [],
        "dataset_keywords": [],
        "value_groups": [],
        "analysis_rules": [],
        "join_rules": [],
        "notes": [],
    }

    for path in sorted(DOMAIN_REGISTRY_ENTRIES_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        normalized = _normalize_entry_payload(payload, str(payload.get("raw_text", "")))
        registry["entries"].append(normalized)
        registry["dataset_keywords"].extend(normalized.get("dataset_keywords", []))
        registry["value_groups"].extend(normalized.get("value_groups", []))
        registry["analysis_rules"].extend(normalized.get("analysis_rules", []))
        registry["join_rules"].extend(normalized.get("join_rules", []))
        registry["notes"].extend(normalized.get("notes", []))

    return registry


def validate_domain_payload(payload: Dict[str, Any], registry: Dict[str, Any] | None = None) -> List[Dict[str, str]]:
    registry = registry or load_domain_registry()
    issues: List[Dict[str, str]] = []

    for item in payload.get("dataset_keywords", []):
        dataset_key = item.get("dataset_key", "")
        if dataset_key not in DATASET_METADATA:
            issues.append({"severity": "error", "message": f"Unknown dataset key: {dataset_key}"})
        for keyword in item.get("keywords", []):
            normalized_keyword = normalize_text(keyword)
            owner = _keyword_owners(registry).get(normalized_keyword)
            if owner and owner != dataset_key:
                issues.append({"severity": "error", "message": f"Keyword conflict: `{keyword}` is already used by `{owner}`."})

    for group in payload.get("value_groups", []):
        if group.get("field") not in SUPPORTED_VALUE_FIELDS:
            issues.append({"severity": "error", "message": f"Unsupported field for value group: {group.get('field')}"})
        if not group.get("canonical"):
            issues.append({"severity": "error", "message": "Value group requires `canonical`."})

    for rule in payload.get("analysis_rules", []):
        if not rule.get("name"):
            issues.append({"severity": "error", "message": "Analysis rule requires `name`."})
        if not rule.get("required_datasets"):
            issues.append({"severity": "warning", "message": f"Analysis rule `{rule.get('name', 'unknown')}` has no required_datasets."})
        if rule.get("calculation_mode", "") not in VALID_CALCULATION_MODES:
            issues.append({"severity": "warning", "message": f"Unknown calculation_mode in `{rule.get('name', 'unknown')}`."})

    for rule in payload.get("join_rules", []):
        if not rule.get("base_dataset") or not rule.get("join_dataset"):
            issues.append({"severity": "error", "message": "Join rule requires both base_dataset and join_dataset."})
        if rule.get("join_type", "left") not in VALID_JOIN_TYPES:
            issues.append({"severity": "warning", "message": f"Unknown join type `{rule.get('join_type')}`. Using `left`."})

    return issues


def _detect_join_keys_from_text(raw_text: str) -> List[str]:
    candidates = ["WORK_DT", "OPER_NAME", "MODE", "FAMILY", "FACTORY", "ORG", "TECH", "DEN", "LEAD"]
    normalized = normalize_text(raw_text)
    return [candidate for candidate in candidates if normalize_text(candidate) in normalized]


def _infer_join_type_from_text(raw_text: str) -> str:
    normalized = normalize_text(raw_text)
    if "inner" in normalized:
        return "inner"
    if "outer" in normalized:
        return "outer"
    if "right" in normalized:
        return "right"
    return "left"


def _infer_join_rules_from_text(raw_text: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    join_rules: List[Dict[str, Any]] = []
    for analysis_rule in payload.get("analysis_rules", []):
        datasets = analysis_rule.get("required_datasets", [])
        if len(datasets) < 2:
            continue
        join_keys = _detect_join_keys_from_text(raw_text) or ["WORK_DT", "OPER_NAME"]
        join_rules.append(
            {
                "name": f"{datasets[0]}_{datasets[1]}_join",
                "base_dataset": datasets[0],
                "join_dataset": datasets[1],
                "join_type": _infer_join_type_from_text(raw_text),
                "join_keys": join_keys,
                "description": f"Inferred from free-text note: {raw_text[:80]}",
                "source": "custom",
            }
        )
    return join_rules


def parse_domain_text_to_payload(raw_text: str) -> Dict[str, Any]:
    prompt = f"""Extract a structured manufacturing domain note into JSON only.

Fields:
- title
- dataset_keywords: [{{dataset_key, keywords}}]
- value_groups: [{{field, canonical, synonyms, values, description}}]
- analysis_rules: [{{name, display_name, synonyms, required_datasets, required_columns, source_columns, calculation_mode, output_column, default_group_by, condition, decision_rule, formula, pandas_hint, description}}]
- join_rules: [{{name, base_dataset, join_dataset, join_type, join_keys, description}}]
- notes

Text:
{raw_text}
"""

    try:
        llm = _get_llm_for_task("domain_registry_parse")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        parsed = _parse_json_block(_extract_text_from_response(response.content))
    except Exception:
        parsed = {}

    normalized = _normalize_entry_payload(parsed, raw_text)
    if not normalized.get("join_rules"):
        normalized["join_rules"] = _infer_join_rules_from_text(raw_text, normalized)
    return normalized


def preview_domain_submission(raw_text: str) -> Dict[str, Any]:
    payload = parse_domain_text_to_payload(raw_text)
    issues = validate_domain_payload(payload)
    return {"success": True, "payload": payload, "issues": issues, "can_save": not any(item["severity"] == "error" for item in issues)}


def register_domain_submission(raw_text: str) -> Dict[str, Any]:
    preview = preview_domain_submission(raw_text)
    if not preview["can_save"]:
        return {"success": False, "payload": preview["payload"], "issues": preview["issues"], "message": "Validation failed."}

    payload = preview["payload"]
    _ensure_registry_dirs()
    path = DOMAIN_REGISTRY_ENTRIES_DIR / f"{payload['id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"success": True, "payload": payload, "issues": preview["issues"], "message": "Saved successfully."}


def delete_domain_entry(entry_id: str) -> Dict[str, Any]:
    path = DOMAIN_REGISTRY_ENTRIES_DIR / f"{entry_id}.json"
    if not path.exists():
        return {"success": False, "deleted": False, "message": "Entry not found."}
    path.unlink()
    return {"success": True, "deleted": True, "message": "Deleted successfully."}


def list_domain_entries() -> List[Dict[str, Any]]:
    return load_domain_registry()["entries"]


def get_dataset_keyword_map() -> Dict[str, List[str]]:
    registry = load_domain_registry()
    keyword_map = _build_builtin_dataset_keywords()
    for item in registry.get("dataset_keywords", []):
        dataset_key = item["dataset_key"]
        keyword_map.setdefault(dataset_key, [])
        for keyword in item["keywords"]:
            if keyword not in keyword_map[dataset_key]:
                keyword_map[dataset_key].append(keyword)
    return keyword_map


def get_registered_value_groups(field_name: str | None = None, include_builtin: bool = False) -> List[Dict[str, Any]]:
    registry = load_domain_registry()
    groups: List[Dict[str, Any]] = []
    if include_builtin:
        builtin = _build_builtin_value_groups()
        if field_name:
            groups.extend(builtin.get(field_name, []))
        else:
            for values in builtin.values():
                groups.extend(values)
    for group in registry.get("value_groups", []):
        if field_name and group.get("field") != field_name:
            continue
        groups.append(group)
    return groups


def expand_registered_values(field_name: str, raw_values: Any) -> List[str] | None:
    normalized_field = _normalize_field_name(field_name)
    requested_values = _as_list(raw_values)
    if not requested_values:
        return None

    expanded: List[str] = []
    for raw_value in requested_values:
        matched = False
        normalized_raw = normalize_text(raw_value)
        for group in get_registered_value_groups(normalized_field, include_builtin=True):
            aliases = [group.get("canonical", ""), *group.get("synonyms", []), *group.get("values", [])]
            if any(normalized_raw == normalize_text(alias) for alias in aliases):
                expanded.extend(group.get("values", []))
                matched = True
                break
        if not matched:
            expanded.append(raw_value)
    expanded = _dedupe(expanded)
    return expanded or None


def detect_registered_values(field_name: str, text: str) -> List[str] | None:
    normalized_field = _normalize_field_name(field_name)
    normalized_text_value = normalize_text(text)
    detected: List[str] = []
    for group in get_registered_value_groups(normalized_field, include_builtin=True):
        aliases = [group.get("canonical", ""), *group.get("synonyms", []), *group.get("values", [])]
        if any(normalize_text(alias) in normalized_text_value for alias in aliases if str(alias).strip()):
            detected.extend(group.get("values", []))
    detected = _dedupe(detected)
    return detected or None


def get_registered_analysis_rules(include_builtin: bool = True) -> List[Dict[str, Any]]:
    registry = load_domain_registry()
    return [*(DEFAULT_ANALYSIS_RULES if include_builtin else []), *registry.get("analysis_rules", [])]


def get_registered_join_rules(include_builtin: bool = True) -> List[Dict[str, Any]]:
    registry = load_domain_registry()
    return [*(DEFAULT_JOIN_RULES if include_builtin else []), *registry.get("join_rules", [])]


def _normalize_compact_text(value: Any) -> str:
    return normalize_text(str(value or "")).replace(" ", "")


def match_registered_analysis_rules(query_text: str, include_builtin: bool = True) -> List[Dict[str, Any]]:
    normalized = _normalize_compact_text(query_text)
    matched: List[Dict[str, Any]] = []
    for rule in get_registered_analysis_rules(include_builtin=include_builtin):
        candidates = [rule.get("name", ""), rule.get("display_name", ""), *rule.get("synonyms", [])]
        if any(_normalize_compact_text(candidate) and _normalize_compact_text(candidate) in normalized for candidate in candidates):
            matched.append(rule)
    return matched


def format_analysis_rule_for_prompt(rule: Dict[str, Any]) -> str:
    return (
        f"- name={rule.get('name', '')}, "
        f"display_name={rule.get('display_name', '')}, "
        f"required_datasets={rule.get('required_datasets', [])}, "
        f"required_columns={rule.get('required_columns', [])}, "
        f"calculation_mode={rule.get('calculation_mode', '')}, "
        f"output_column={rule.get('output_column', '')}, "
        f"default_group_by={rule.get('default_group_by', [])}, "
        f"condition={rule.get('condition', '')}, "
        f"decision_rule={rule.get('decision_rule', '')}, "
        f"formula={rule.get('formula', '')}, "
        f"source_columns={rule.get('source_columns', [])}"
    )


def build_registered_domain_prompt() -> str:
    registry = load_domain_registry()
    lines = ["Custom domain registry summary:"]

    dataset_keyword_map = get_dataset_keyword_map()
    if dataset_keyword_map:
        lines.append("Dataset keywords:")
        for dataset_key, keywords in dataset_keyword_map.items():
            if keywords:
                lines.append(f"- {dataset_key}: {', '.join(keywords)}")

    value_groups = get_registered_value_groups(include_builtin=False)
    if value_groups:
        lines.append("Custom value groups:")
        for group in value_groups:
            lines.append(
                f"- field={group.get('field')}, canonical={group.get('canonical')}, "
                f"values={group.get('values', [])}, synonyms={group.get('synonyms', [])}"
            )

    analysis_rules = registry.get("analysis_rules", [])
    if analysis_rules:
        lines.append("Custom analysis rules:")
        for rule in analysis_rules:
            lines.append(format_analysis_rule_for_prompt(rule))

    join_rules = registry.get("join_rules", [])
    if join_rules:
        lines.append("Custom join rules:")
        for rule in join_rules:
            lines.append(
                f"- {rule.get('base_dataset')} -> {rule.get('join_dataset')}, "
                f"type={rule.get('join_type')}, keys={rule.get('join_keys', [])}"
            )

    notes = registry.get("notes", [])
    if notes:
        lines.append("Notes:")
        for note in notes:
            lines.append(f"- {note}")

    if len(lines) == 1:
        lines.append("- No custom registry entries.")
    return "\n".join(lines)


def get_domain_registry_summary() -> Dict[str, Any]:
    registry = load_domain_registry()
    return {
        "custom_entry_count": len(registry["entries"]),
        "custom_dataset_keyword_count": len(registry["dataset_keywords"]),
        "custom_value_group_count": len(registry["value_groups"]),
        "custom_analysis_rule_count": len(registry["analysis_rules"]),
        "custom_join_rule_count": len(registry["join_rules"]),
        "builtin_analysis_rule_count": len(DEFAULT_ANALYSIS_RULES),
        "builtin_join_rule_count": len(DEFAULT_JOIN_RULES),
        "builtin_value_group_count": sum(len(items) for items in _build_builtin_value_groups().values()),
    }
