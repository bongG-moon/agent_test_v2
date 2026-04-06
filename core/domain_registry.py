from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from langchain_core.messages import HumanMessage, SystemMessage

from .config import SYSTEM_PROMPT, get_llm
from .domain_knowledge import (
    DATASET_METADATA,
    DEN_GROUPS,
    MODE_GROUPS,
    PKG_TYPE1_GROUPS,
    PKG_TYPE2_GROUPS,
    PROCESS_GROUPS,
    SPECIAL_PRODUCT_ALIASES,
    TECH_GROUPS,
)
from .filter_utils import normalize_text


def _get_llm_for_task(task: str):
    try:
        return get_llm(task=task)
    except TypeError:
        return get_llm()


ROOT_DIR = Path(__file__).resolve().parents[1]
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
        "display_name": "달성률",
        "synonyms": ["달성율", "달성률", "목표 대비 생산", "achievement rate"],
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
        "pandas_hint": (
            "grouped = df.groupby('OPER_NAME', as_index=False).agg("
            "production=('production', 'sum'), target=('target', 'sum')); "
            "grouped['achievement_rate'] = grouped['production'] / grouped['target']; result = grouped"
        ),
        "description": "생산과 목표를 같이 불러와 비율을 계산합니다.",
        "source": "builtin",
    },
    {
        "name": "yield_rate",
        "display_name": "수율",
        "synonyms": ["수율", "양품률", "yield", "yield rate"],
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
        "pandas_hint": "result = df.groupby('OPER_NAME', as_index=False).agg(yield_rate=('yield_rate', 'mean'))",
        "description": "수율 데이터셋으로 평균 또는 비교 분석을 수행합니다.",
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
            normalized_columns.append(
                {
                    "dataset_key": dataset_key,
                    "column": column,
                    "role": role,
                }
            )
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
        "source": "custom",
    }


def _normalize_join_rule(raw_rule: Dict[str, Any]) -> Dict[str, Any]:
    join_type = normalize_text(raw_rule.get("join_type"))
    if join_type not in VALID_JOIN_TYPES:
        join_type = "left" if join_type else ""
    return {
        "name": str(raw_rule.get("name", "")).strip(),
        "base_dataset": normalize_text(raw_rule.get("base_dataset")),
        "join_dataset": normalize_text(raw_rule.get("join_dataset")),
        "join_type": join_type,
        "join_keys": _dedupe(_as_list(raw_rule.get("join_keys"))),
        "description": str(raw_rule.get("description", "")).strip(),
        "source": "custom",
    }


def _normalize_entry_payload(payload: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    raw_lines = str(raw_text or "").strip().splitlines()
    fallback_title = raw_lines[0][:60] if raw_lines else "user domain note"
    title = str(payload.get("title", "")).strip() or fallback_title
    dataset_keywords = [
        _normalize_dataset_keyword_rule(item)
        for item in payload.get("dataset_keywords", [])
        if isinstance(item, dict)
    ]
    value_groups = [
        _normalize_value_group(item)
        for item in payload.get("value_groups", [])
        if isinstance(item, dict)
    ]
    analysis_rules = [
        _normalize_analysis_rule(item)
        for item in payload.get("analysis_rules", [])
        if isinstance(item, dict)
    ]
    join_rules = [
        _normalize_join_rule(item)
        for item in payload.get("join_rules", [])
        if isinstance(item, dict)
    ]
    notes = _dedupe(_as_list(payload.get("notes")))
    return {
        "title": title,
        "dataset_keywords": [item for item in dataset_keywords if item["dataset_key"] and item["keywords"]],
        "value_groups": [item for item in value_groups if item["field"] and item["canonical"] and item["values"]],
        "analysis_rules": [item for item in analysis_rules if item["name"] and item["synonyms"]],
        "join_rules": [item for item in join_rules if item["name"] and item["base_dataset"] and item["join_dataset"]],
        "notes": notes,
    }


def _build_builtin_value_groups() -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {
        "process_name": [],
        "mode": [],
        "den": [],
        "tech": [],
        "pkg_type1": [],
        "pkg_type2": [],
        "product_name": [],
    }

    for group in PROCESS_GROUPS.values():
        groups["process_name"].append(
            {
                "field": "process_name",
                "canonical": group["group_name"],
                "synonyms": _dedupe(group.get("synonyms", [])),
                "values": _dedupe(group.get("actual_values", [])),
                "source": "builtin",
            }
        )

    for field_name, collection in [
        ("mode", MODE_GROUPS),
        ("den", DEN_GROUPS),
        ("tech", TECH_GROUPS),
        ("pkg_type1", PKG_TYPE1_GROUPS),
        ("pkg_type2", PKG_TYPE2_GROUPS),
    ]:
        for canonical, group in collection.items():
            groups[field_name].append(
                {
                    "field": field_name,
                    "canonical": canonical,
                    "synonyms": _dedupe(group.get("synonyms", [])),
                    "values": _dedupe(group.get("actual_values", [])),
                    "source": "builtin",
                }
            )

    groups["product_name"].append(
        {
            "field": "product_name",
            "canonical": "HBM_OR_3DS",
            "synonyms": _dedupe(["HBM_OR_3DS", *SPECIAL_PRODUCT_ALIASES["HBM_OR_3DS"]]),
            "values": ["HBM_OR_3DS"],
            "source": "builtin",
        }
    )
    groups["product_name"].append(
        {
            "field": "product_name",
            "canonical": "AUTO_PRODUCT",
            "synonyms": _dedupe(["AUTO_PRODUCT", *SPECIAL_PRODUCT_ALIASES["AUTO_PRODUCT"]]),
            "values": ["AUTO_PRODUCT"],
            "source": "builtin",
        }
    )
    return groups


def _build_builtin_dataset_keywords() -> Dict[str, List[str]]:
    return {dataset_key: _dedupe(meta.get("keywords", [])) for dataset_key, meta in DATASET_METADATA.items()}


def _keyword_owners(registry: Dict[str, Any]) -> Dict[str, str]:
    owners: Dict[str, str] = {}
    for dataset_key, keywords in _build_builtin_dataset_keywords().items():
        for keyword in keywords:
            owners[normalize_text(keyword)] = dataset_key

    for item in registry.get("dataset_keywords", []):
        dataset_key = item.get("dataset_key", "")
        for keyword in item.get("keywords", []):
            owners[normalize_text(keyword)] = dataset_key
    return owners


def _group_signature(group: Dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(normalize_text(value) for value in group.get("values", [])))


def _analysis_rule_signature(rule: Dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...], str, str]:
    return (
        tuple(sorted(normalize_text(item) for item in rule.get("required_datasets", []))),
        tuple(sorted(normalize_text(item) for item in rule.get("required_columns", []))),
        normalize_text(rule.get("formula", "")),
        normalize_text(rule.get("decision_rule", "")),
    )


def _existing_groups_for_field(registry: Dict[str, Any], field_name: str) -> List[Dict[str, Any]]:
    builtins = _build_builtin_value_groups().get(field_name, [])
    customs = [item for item in registry.get("value_groups", []) if item.get("field") == field_name]
    return [*builtins, *customs]


def _existing_analysis_rules(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [*DEFAULT_ANALYSIS_RULES, *registry.get("analysis_rules", [])]


def _join_rule_signature(rule: Dict[str, Any]) -> tuple[str, str, str, tuple[str, ...]]:
    return (
        normalize_text(rule.get("base_dataset", "")),
        normalize_text(rule.get("join_dataset", "")),
        normalize_text(rule.get("join_type", "")),
        tuple(sorted(normalize_text(item) for item in rule.get("join_keys", []))),
    )


def _existing_join_rules(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [*DEFAULT_JOIN_RULES, *registry.get("join_rules", [])]


def load_domain_registry() -> Dict[str, Any]:
    _ensure_registry_dirs()

    entries: List[Dict[str, Any]] = []
    dataset_keywords: List[Dict[str, Any]] = []
    value_groups: List[Dict[str, Any]] = []
    analysis_rules: List[Dict[str, Any]] = []
    join_rules: List[Dict[str, Any]] = []
    notes: List[str] = []
    loaded_files: List[str] = []

    for path in sorted(DOMAIN_REGISTRY_ENTRIES_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        loaded_files.append(path.name)
        entries.append(payload)

        entry_id = str(payload.get("id", path.stem))
        title = str(payload.get("title", entry_id))

        for item in payload.get("dataset_keywords", []):
            dataset_keywords.append({**item, "entry_id": entry_id, "entry_title": title})
        for item in payload.get("value_groups", []):
            value_groups.append({**item, "entry_id": entry_id, "entry_title": title})
        for item in payload.get("analysis_rules", []):
            analysis_rules.append({**item, "entry_id": entry_id, "entry_title": title})
        for item in payload.get("join_rules", []):
            join_rules.append({**item, "entry_id": entry_id, "entry_title": title})
        for item in payload.get("notes", []):
            notes.append(str(item))

    return {
        "entries": entries,
        "dataset_keywords": dataset_keywords,
        "value_groups": value_groups,
        "analysis_rules": analysis_rules,
        "join_rules": join_rules,
        "notes": _dedupe(notes),
        "loaded_files": loaded_files,
    }


def validate_domain_payload(payload: Dict[str, Any], registry: Dict[str, Any] | None = None) -> List[Dict[str, str]]:
    registry = registry or load_domain_registry()
    issues: List[Dict[str, str]] = []
    keyword_owners = _keyword_owners(registry)
    seen_keywords: Dict[str, str] = {}
    seen_group_aliases: Dict[tuple[str, str], Dict[str, Any]] = {}
    seen_rule_aliases: Dict[str, Dict[str, Any]] = {}
    seen_join_pairs: Dict[tuple[str, str], Dict[str, Any]] = {}

    for item in payload.get("dataset_keywords", []):
        dataset_key = item.get("dataset_key", "")
        if dataset_key not in DATASET_METADATA:
            issues.append({"severity": "error", "message": f"Unsupported dataset_key: {dataset_key}"})
            continue
        for keyword in item.get("keywords", []):
            normalized_keyword = normalize_text(keyword)
            if normalized_keyword in seen_keywords:
                issues.append({"severity": "warning", "message": f"Duplicate keyword in the same submission: {keyword}"})
                continue
            seen_keywords[normalized_keyword] = dataset_key
            owner = keyword_owners.get(normalized_keyword)
            if owner and owner != dataset_key:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"Keyword `{keyword}` is already connected to dataset `{owner}`.",
                    }
                )
            elif owner == dataset_key:
                issues.append(
                    {
                        "severity": "warning",
                        "message": f"Keyword `{keyword}` is already registered for dataset `{dataset_key}`.",
                    }
                )

    for item in payload.get("value_groups", []):
        field_name = item.get("field", "")
        if field_name not in SUPPORTED_VALUE_FIELDS:
            issues.append({"severity": "error", "message": f"Unsupported field: {field_name}"})
            continue
        existing_groups = _existing_groups_for_field(registry, field_name)
        for alias in item.get("synonyms", []):
            normalized_alias = normalize_text(alias)
            alias_key = (field_name, normalized_alias)
            if alias_key in seen_group_aliases:
                issues.append({"severity": "warning", "message": f"Duplicate alias in the same submission: {alias}"})
                continue
            seen_group_aliases[alias_key] = item
            for existing in existing_groups:
                existing_aliases = [existing.get("canonical", ""), *existing.get("synonyms", [])]
                if normalized_alias not in {normalize_text(value) for value in existing_aliases}:
                    continue
                same_signature = _group_signature(existing) == _group_signature(item)
                same_canonical = normalize_text(existing.get("canonical", "")) == normalize_text(item.get("canonical", ""))
                if same_signature and same_canonical:
                    issues.append({"severity": "warning", "message": f"Alias `{alias}` already exists with the same meaning."})
                else:
                    issues.append(
                        {
                            "severity": "error",
                            "message": f"Alias `{alias}` conflicts with an existing `{field_name}` group.",
                        }
                    )
                break

    for item in payload.get("analysis_rules", []):
        rule_name = item.get("display_name") or item.get("name")
        calculation_mode = item.get("calculation_mode", "")
        if not item.get("formula") and not item.get("pandas_hint") and not item.get("decision_rule"):
            issues.append(
                {
                    "severity": "error",
                    "message": f"Analysis rule `{rule_name}` needs a formula, pandas_hint, or decision_rule.",
                }
            )
        if calculation_mode and calculation_mode != "custom" and not item.get("source_columns"):
            issues.append(
                {
                    "severity": "warning",
                    "message": f"Analysis rule `{rule_name}` uses calculation_mode `{calculation_mode}` but has no source_columns hint.",
                }
            )
        if calculation_mode in {"condition_flag", "threshold_flag", "count_if", "sum_if", "mean_if"} and not item.get("condition"):
            issues.append(
                {
                    "severity": "warning",
                    "message": f"Analysis rule `{rule_name}` uses calculation_mode `{calculation_mode}` but has no condition text.",
                }
            )
        if calculation_mode in {"condition_flag", "threshold_flag"} and not item.get("decision_rule"):
            issues.append(
                {
                    "severity": "warning",
                    "message": f"Analysis rule `{rule_name}` looks like a status decision rule but has no decision_rule text.",
                }
            )
        if calculation_mode and not item.get("output_column"):
            issues.append(
                {
                    "severity": "warning",
                    "message": f"Analysis rule `{rule_name}` is missing output_column, so the derived column name may be unstable.",
                }
            )
        invalid_datasets = [key for key in item.get("required_datasets", []) if key not in DATASET_METADATA]
        if invalid_datasets:
            issues.append(
                {
                    "severity": "error",
                    "message": f"Analysis rule `{rule_name}` references unsupported datasets: {', '.join(invalid_datasets)}",
                }
            )
        for source_column in item.get("source_columns", []):
            dataset_key = source_column.get("dataset_key", "")
            if dataset_key and dataset_key not in DATASET_METADATA:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"Analysis rule `{rule_name}` references unsupported source dataset `{dataset_key}`.",
                    }
                )
        unsafe_tokens = ["import ", "exec(", "eval(", "open(", "os.", "subprocess", "requests", "http"]
        combined_text = " ".join(
            [
                item.get("formula", ""),
                item.get("pandas_hint", ""),
                item.get("condition", ""),
                item.get("decision_rule", ""),
            ]
        ).lower()
        if any(token in combined_text for token in unsafe_tokens):
            issues.append(
                {
                    "severity": "error",
                    "message": f"Analysis rule `{rule_name}` includes unsafe text.",
                }
            )

        existing_rules = _existing_analysis_rules(registry)
        for alias in item.get("synonyms", []):
            normalized_alias = normalize_text(alias)
            if normalized_alias in seen_rule_aliases:
                issues.append({"severity": "warning", "message": f"Duplicate analysis-rule alias in the same submission: {alias}"})
                continue
            seen_rule_aliases[normalized_alias] = item
            for existing in existing_rules:
                existing_aliases = [existing.get("name", ""), existing.get("display_name", ""), *existing.get("synonyms", [])]
                if normalized_alias not in {normalize_text(value) for value in existing_aliases}:
                    continue
                same_signature = _analysis_rule_signature(existing) == _analysis_rule_signature(item)
                same_name = normalize_text(existing.get("name", "")) == normalize_text(item.get("name", ""))
                if same_signature and same_name:
                    issues.append({"severity": "warning", "message": f"Analysis rule alias `{alias}` already exists with the same meaning."})
                else:
                    issues.append(
                        {
                            "severity": "error",
                            "message": f"Analysis rule alias `{alias}` conflicts with an existing rule.",
                        }
                )
                break

    for item in payload.get("join_rules", []):
        rule_name = item.get("name") or f"{item.get('base_dataset')}->{item.get('join_dataset')}"
        base_dataset = item.get("base_dataset", "")
        join_dataset = item.get("join_dataset", "")
        join_type = item.get("join_type", "")
        join_keys = item.get("join_keys", [])

        if base_dataset not in DATASET_METADATA:
            issues.append({"severity": "error", "message": f"Join rule `{rule_name}` uses unsupported base_dataset `{base_dataset}`."})
        if join_dataset not in DATASET_METADATA:
            issues.append({"severity": "error", "message": f"Join rule `{rule_name}` uses unsupported join_dataset `{join_dataset}`."})
        if join_type not in VALID_JOIN_TYPES:
            issues.append({"severity": "error", "message": f"Join rule `{rule_name}` uses unsupported join_type `{join_type}`."})
        if not join_keys:
            issues.append({"severity": "error", "message": f"Join rule `{rule_name}` needs at least one join key."})

        pair_key = (base_dataset, join_dataset)
        if pair_key in seen_join_pairs:
            previous = seen_join_pairs[pair_key]
            if _join_rule_signature(previous) == _join_rule_signature(item):
                issues.append(
                    {
                        "severity": "warning",
                        "message": f"Join rule `{rule_name}` is duplicated in the same submission.",
                    }
                )
            else:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"Join rule `{rule_name}` conflicts with another join rule for `{base_dataset} -> {join_dataset}` in the same submission.",
                    }
                )
            continue
        seen_join_pairs[pair_key] = item

        for existing in _existing_join_rules(registry):
            same_pair = (
                normalize_text(existing.get("base_dataset", "")) == normalize_text(base_dataset)
                and normalize_text(existing.get("join_dataset", "")) == normalize_text(join_dataset)
            )
            if not same_pair:
                continue
            if _join_rule_signature(existing) == _join_rule_signature(item):
                issues.append(
                    {
                        "severity": "warning",
                        "message": f"Join rule `{rule_name}` already exists with the same meaning.",
                    }
                )
            else:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"Join rule `{rule_name}` conflicts with an existing rule for `{base_dataset} -> {join_dataset}`.",
                    }
                )
            break

    return issues


JOIN_KEY_KEYWORDS = {
    "WORK_DT": ["WORK_DT", "date", "날짜", "일자"],
    "OPER_NAME": ["OPER_NAME", "process", "공정"],
    "OPER_NUM": ["OPER_NUM", "oper_num", "공정번호"],
    "MODE": ["MODE", "mode"],
    "DEN": ["DEN", "den"],
    "TECH": ["TECH", "tech"],
    "LEAD": ["LEAD", "lead"],
    "MCP_NO": ["MCP_NO", "mcp", "mcp_no"],
    "PKG_TYPE1": ["PKG_TYPE1", "pkg_type1", "pkg1"],
    "PKG_TYPE2": ["PKG_TYPE2", "pkg_type2", "pkg2"],
    "FAMILY": ["FAMILY", "family"],
    "FACTORY": ["FACTORY", "factory"],
    "ORG": ["ORG", "org"],
}


def _detect_join_keys_from_text(raw_text: str) -> List[str]:
    normalized_text = normalize_text(raw_text)
    join_keys: List[str] = []
    for column_name, aliases in JOIN_KEY_KEYWORDS.items():
        if any(normalize_text(alias) in normalized_text for alias in aliases):
            join_keys.append(column_name)
    return _dedupe(join_keys)


def _infer_join_type_from_text(raw_text: str) -> str:
    normalized_text = normalize_text(raw_text)
    if "left join" in normalized_text or "leftjoin" in normalized_text or "left" in normalized_text:
        return "left"
    if "right join" in normalized_text or "rightjoin" in normalized_text or "right" in normalized_text:
        return "right"
    if "inner join" in normalized_text or "innerjoin" in normalized_text or "inner" in normalized_text:
        return "inner"
    if "outer join" in normalized_text or "outerjoin" in normalized_text or "outer" in normalized_text:
        return "outer"
    if any(token in normalized_text for token in ["기준으로 맞춰", "기준으로 결합", "같은", "맞춰서", "붙여"]):
        return "left"
    return ""


def _infer_join_rules_from_text(raw_text: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    existing_rules = payload.get("join_rules", [])
    if existing_rules:
        return existing_rules

    normalized_text = normalize_text(raw_text)
    dataset_mentions: List[str] = []
    for dataset_key in DATASET_METADATA:
        if normalize_text(dataset_key) in normalized_text:
            dataset_mentions.append(dataset_key)

    analysis_required = []
    for rule in payload.get("analysis_rules", []):
        analysis_required.extend(rule.get("required_datasets", []))

    dataset_keys = _dedupe([*dataset_mentions, *analysis_required])
    if len(dataset_keys) < 2:
        return []

    join_type = _infer_join_type_from_text(raw_text)
    join_keys = _detect_join_keys_from_text(raw_text)
    if not join_keys:
        return []
    if not join_type:
        join_type = "left"

    base_dataset = dataset_keys[0]
    join_rules: List[Dict[str, Any]] = []
    for join_dataset in dataset_keys[1:]:
        join_rules.append(
            {
                "name": f"{base_dataset}_{join_dataset}_join",
                "base_dataset": base_dataset,
                "join_dataset": join_dataset,
                "join_type": join_type,
                "join_keys": join_keys,
                "description": "Auto-inferred from the free-form domain note.",
                "source": "custom",
            }
        )
    return join_rules


def parse_domain_text_to_payload(raw_text: str) -> Dict[str, Any]:
    prompt = f"""You are converting free-form manufacturing domain notes into a structured registry payload.
Return JSON only.

Supported dataset keys:
{", ".join(DATASET_METADATA.keys())}

Supported value-group fields:
{", ".join(sorted(SUPPORTED_VALUE_FIELDS))}

Rules:
- Convert free-form aliases into structured dataset keyword rules, value groups, and analysis rules.
- Use `value_groups` when the user is defining aliases or grouped meanings for filter values.
- Use `analysis_rules` when the user is describing a derived metric, a threshold rule, a status rule, or a simple decision rule.
- If the user explains which dataset, which column, what condition, or how to calculate, preserve that meaning in the structured fields.
- `values` must contain the concrete values that the retrieval layer should finally use.
- `required_datasets` must use only the supported dataset keys.
- `source_columns` should describe dataset/column/role pairs when the user explains a calculation.
- `calculation_mode` can be ratio, difference, sum, mean, count, condition_flag, threshold_flag, count_if, sum_if, mean_if, or custom.
- `condition` should contain the logical condition text when the user defines a threshold or flag rule.
- `decision_rule` should describe how the final result is decided when the rule returns labels such as 정상/이상.
- `output_column` should name the derived column or final flag column when the user implies one.
- `default_group_by` can be used when the user strongly implies the default aggregation grain.
- If something is only a note, put it into `notes`.
- Do not invent unsupported dataset keys or fields.

Examples:
- "생산 달성률은 production 테이블의 production과 target 테이블의 target으로 production / target 을 계산해줘."
  -> analysis_rules should include required_datasets, source_columns, calculation_mode="ratio", and formula.
- "HOLD 이상여부는 wip 테이블의 상태가 HOLD, REWORK, WAIT_MATERIAL, WAIT_QA 중 하나면 이상 아니면 정상으로 봐줘."
  -> analysis_rules should include required_datasets=["wip"], source_columns for 상태, calculation_mode="condition_flag", condition, and decision_rule.
- "장비 가동 이상여부는 equipment 테이블의 가동률이 85 미만이면 이상이야."
  -> analysis_rules should include required_datasets=["equipment"], source_columns for 가동률, calculation_mode="threshold_flag", condition, and decision_rule.

Return this schema:
{{
  "title": "short title",
  "dataset_keywords": [
    {{"dataset_key": "yield", "keywords": ["양품률"]}}
  ],
  "value_groups": [
    {{
      "field": "process_name",
      "canonical": "후공정A",
      "synonyms": ["후공정A"],
      "values": ["D/A1", "D/A2"],
      "description": "optional"
    }}
  ],
  "analysis_rules": [
    {{
      "name": "achievement_rate",
      "display_name": "달성률",
      "synonyms": ["달성률"],
      "required_datasets": ["production", "target"],
      "required_columns": ["production", "target"],
      "source_columns": [
        {{"dataset_key": "production", "column": "production", "role": "numerator"}},
        {{"dataset_key": "target", "column": "target", "role": "denominator"}}
      ],
      "calculation_mode": "ratio",
      "output_column": "achievement_rate",
      "default_group_by": ["OPER_NAME"],
      "condition": "",
      "decision_rule": "",
      "formula": "production / target",
      "pandas_hint": "groupby and calculate ratio",
      "description": "optional"
    }}
  ],
  "notes": ["optional note"]
}}

User text:
{raw_text}
"""

    try:
        llm = _get_llm_for_task("domain_registry_parse")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        parsed = _parse_json_block(_extract_text_from_response(response.content))
    except Exception:
        parsed = {}
    normalized_payload = _normalize_entry_payload(parsed, raw_text)
    normalized_payload["join_rules"] = _infer_join_rules_from_text(raw_text, normalized_payload)
    return normalized_payload


def preview_domain_submission(raw_text: str) -> Dict[str, Any]:
    payload = parse_domain_text_to_payload(raw_text)
    registry = load_domain_registry()
    issues = validate_domain_payload(payload, registry)
    return {
        "success": True,
        "raw_text": raw_text,
        "payload": payload,
        "issues": issues,
        "can_save": not any(item["severity"] == "error" for item in issues),
    }


def register_domain_submission(raw_text: str) -> Dict[str, Any]:
    preview = preview_domain_submission(raw_text)
    if not preview.get("can_save"):
        return {**preview, "saved": False}

    _ensure_registry_dirs()
    payload = preview["payload"]
    entry_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    entry = {
        "id": entry_id,
        "title": payload["title"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "raw_text": raw_text,
        "dataset_keywords": payload.get("dataset_keywords", []),
        "value_groups": payload.get("value_groups", []),
        "analysis_rules": payload.get("analysis_rules", []),
        "join_rules": payload.get("join_rules", []),
        "notes": payload.get("notes", []),
        "issues": preview.get("issues", []),
    }
    target_path = DOMAIN_REGISTRY_ENTRIES_DIR / f"{entry_id}.json"
    target_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**preview, "saved": True, "entry": entry}


def delete_domain_entry(entry_id: str) -> Dict[str, Any]:
    _ensure_registry_dirs()
    target_id = str(entry_id or "").strip()
    if not target_id:
        return {"success": False, "deleted": False, "message": "삭제할 엔트리 id가 비어 있습니다."}

    for path in sorted(DOMAIN_REGISTRY_ENTRIES_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        payload_id = str(payload.get("id", path.stem)).strip()
        if payload_id != target_id and path.stem != target_id:
            continue

        path.unlink(missing_ok=False)
        return {
            "success": True,
            "deleted": True,
            "entry_id": payload_id,
            "title": str(payload.get("title", payload_id)),
            "message": f"엔트리 `{payload_id}` 삭제를 완료했습니다.",
        }

    return {
        "success": False,
        "deleted": False,
        "entry_id": target_id,
        "message": f"엔트리 `{target_id}` 를 찾지 못했습니다.",
    }


def list_domain_entries() -> List[Dict[str, Any]]:
    return load_domain_registry().get("entries", [])


def get_dataset_keyword_map() -> Dict[str, List[str]]:
    keyword_map = _build_builtin_dataset_keywords()
    for item in load_domain_registry().get("dataset_keywords", []):
        keyword_map.setdefault(item["dataset_key"], [])
        for keyword in item.get("keywords", []):
            if keyword not in keyword_map[item["dataset_key"]]:
                keyword_map[item["dataset_key"]].append(keyword)
    return keyword_map


def get_registered_value_groups(field_name: str | None = None, include_builtin: bool = False) -> List[Dict[str, Any]]:
    registry = load_domain_registry()
    items: List[Dict[str, Any]] = []

    if include_builtin:
        for current_field, groups in _build_builtin_value_groups().items():
            if field_name and current_field != field_name:
                continue
            items.extend(groups)

    for item in registry.get("value_groups", []):
        if field_name and item.get("field") != field_name:
            continue
        items.append(item)
    return items


def expand_registered_values(field_name: str, raw_values: Any) -> List[str] | None:
    values = _as_list(raw_values)
    if not values:
        return None

    expanded: List[str] = []
    groups = get_registered_value_groups(field_name)
    for raw_value in values:
        normalized_raw = normalize_text(raw_value)
        matched = False
        for group in groups:
            aliases = [group.get("canonical", ""), *group.get("synonyms", []), *group.get("values", [])]
            if normalized_raw in {normalize_text(alias) for alias in aliases}:
                expanded.extend(group.get("values", []))
                matched = True
                break
        if not matched:
            expanded.append(raw_value)
    expanded = _dedupe(expanded)
    return expanded or None


def detect_registered_values(field_name: str, text: str) -> List[str] | None:
    matched: List[str] = []
    normalized_text = normalize_text(text)
    for group in get_registered_value_groups(field_name):
        aliases = [group.get("canonical", ""), *group.get("synonyms", []), *group.get("values", [])]
        if any(normalize_text(alias) and normalize_text(alias) in normalized_text for alias in aliases):
            matched.extend(group.get("values", []))
    matched = _dedupe(matched)
    return matched or None


def get_registered_analysis_rules(include_builtin: bool = True) -> List[Dict[str, Any]]:
    registry = load_domain_registry()
    if include_builtin:
        return [*DEFAULT_ANALYSIS_RULES, *registry.get("analysis_rules", [])]
    return list(registry.get("analysis_rules", []))


def get_registered_join_rules(include_builtin: bool = True) -> List[Dict[str, Any]]:
    registry = load_domain_registry()
    if include_builtin:
        return [*DEFAULT_JOIN_RULES, *registry.get("join_rules", [])]
    return list(registry.get("join_rules", []))


def _normalize_compact_text(value: Any) -> str:
    normalized = normalize_text(value)
    return normalized.replace(" ", "").replace("_", "").replace("-", "")


def match_registered_analysis_rules(query_text: str, include_builtin: bool = True) -> List[Dict[str, Any]]:
    normalized_query = normalize_text(query_text)
    compact_query = _normalize_compact_text(query_text)
    matched: List[Dict[str, Any]] = []
    for rule in get_registered_analysis_rules(include_builtin=include_builtin):
        aliases = [rule.get("name", ""), rule.get("display_name", ""), *rule.get("synonyms", [])]
        if any(
            (
                normalize_text(alias)
                and (
                    normalize_text(alias) in normalized_query
                    or _normalize_compact_text(alias) in compact_query
                )
            )
            for alias in aliases
        ):
            matched.append(rule)
    return matched


def format_analysis_rule_for_prompt(rule: Dict[str, Any]) -> str:
    source_columns_text = ", ".join(
        f"{item.get('dataset_key')}:{item.get('column')}({item.get('role')})"
        for item in rule.get("source_columns", [])
    ) or "(none)"
    default_group_by_text = ", ".join(rule.get("default_group_by", [])) or "(none)"
    return (
        f"- {rule.get('display_name') or rule.get('name')}: "
        f"required_datasets={', '.join(rule.get('required_datasets', [])) or '(none)'}; "
        f"required_columns={', '.join(rule.get('required_columns', [])) or '(none)'}; "
        f"source_columns={source_columns_text}; "
        f"calculation_mode={rule.get('calculation_mode', '') or '(none)'}; "
        f"output_column={rule.get('output_column', '') or '(none)'}; "
        f"default_group_by={default_group_by_text}; "
        f"condition={rule.get('condition', '') or '(none)'}; "
        f"decision_rule={rule.get('decision_rule', '') or '(none)'}; "
        f"formula={rule.get('formula', '') or '(none)'}; "
        f"pandas_hint={rule.get('pandas_hint', '') or '(none)'}"
    )


def build_registered_domain_prompt() -> str:
    registry = load_domain_registry()
    lines: List[str] = []
    lines.append("Additional custom domain registry:")

    if not registry.get("entries"):
        lines.append("- No custom entries registered.")
        return "\n".join(lines)

    dataset_keywords = registry.get("dataset_keywords", [])
    value_groups = registry.get("value_groups", [])
    analysis_rules = registry.get("analysis_rules", [])
    join_rules = registry.get("join_rules", [])

    if dataset_keywords:
        lines.append("- Custom dataset keywords:")
        for item in dataset_keywords[:20]:
            lines.append(f"  - {item['dataset_key']}: {', '.join(item.get('keywords', []))}")

    if value_groups:
        lines.append("- Custom value groups:")
        for item in value_groups[:20]:
            lines.append(
                f"  - field={item.get('field')}, canonical={item.get('canonical')}, "
                f"synonyms={', '.join(item.get('synonyms', []))}, values={', '.join(item.get('values', []))}"
            )

    if analysis_rules:
        lines.append("- Custom analysis rules:")
        for item in analysis_rules[:20]:
            lines.append(f"  {format_analysis_rule_for_prompt(item)}")

    if join_rules:
        lines.append("- Custom join rules:")
        for item in join_rules[:20]:
            lines.append(
                "  - "
                f"{item.get('base_dataset')} -> {item.get('join_dataset')}: "
                f"how={item.get('join_type') or '(none)'}, "
                f"keys={', '.join(item.get('join_keys', [])) or '(none)'}"
            )

    if registry.get("notes"):
        lines.append("- Custom notes:")
        for note in registry.get("notes", [])[:20]:
            lines.append(f"  - {note}")

    return "\n".join(lines)


def get_domain_registry_summary() -> Dict[str, Any]:
    registry = load_domain_registry()
    return {
        "custom_entry_count": len(registry.get("entries", [])),
        "custom_dataset_keyword_count": len(registry.get("dataset_keywords", [])),
        "custom_value_group_count": len(registry.get("value_groups", [])),
        "custom_analysis_rule_count": len(registry.get("analysis_rules", [])),
        "custom_join_rule_count": len(registry.get("join_rules", [])),
        "custom_notes_count": len(registry.get("notes", [])),
        "builtin_dataset_keyword_count": sum(len(item) for item in _build_builtin_dataset_keywords().values()),
        "builtin_value_group_count": sum(len(item) for item in _build_builtin_value_groups().values()),
        "builtin_analysis_rule_count": len(DEFAULT_ANALYSIS_RULES),
        "builtin_join_rule_count": len(DEFAULT_JOIN_RULES),
    }
