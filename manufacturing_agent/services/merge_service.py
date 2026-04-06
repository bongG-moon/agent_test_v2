"""Merge multiple raw datasets into one analysis-friendly table."""

import re
from typing import Any, Dict, List

import pandas as pd

from ..analysis.helpers import find_requested_dimensions
from ..domain.registry import get_registered_join_rules, match_registered_analysis_rules
from ..shared.filter_utils import normalize_text
from .request_context import raw_dataset_key


KNOWN_DIMENSION_COLUMNS = [
    "WORK_DT",
    "OPER_NAME",
    "怨듭젙援?",
    "?쇱씤",
    "MODE",
    "DEN",
    "TECH",
    "LEAD",
    "MCP_NO",
    "OPER_NUM",
    "PKG_TYPE1",
    "PKG_TYPE2",
    "PKG1",
    "PKG2",
    "TSV_DIE_TYP",
    "FACTORY",
    "FAMILY",
    "ORG",
]

DATE_COLUMNS = {"WORK_DT"}

LIKELY_METRIC_COLUMNS = {
    "production",
    "target",
    "yield_rate",
    "pass_qty",
    "tested_qty",
    "defect_rate",
    "defect_qty",
    "hold_qty",
    "hold_hours",
    "avg_wait_minutes",
    "downtime_minutes",
    "scrap_qty",
    "recipe_temp",
    "recipe_pressure",
    "?섎웾",
    "嫄댁닔",
    "湲덉븸",
}


def should_suffix_metrics(tool_results: List[Dict[str, Any]]) -> bool:
    identifiers = [str(result.get("dataset_key") or result.get("tool_name") or "").split("__", 1)[0] for result in tool_results]
    return len(identifiers) != len(set(identifiers))


def should_exclude_date_from_join(tool_results: List[Dict[str, Any]]) -> bool:
    raw_dataset_keys = [str(result.get("dataset_key", "")).split("__", 1)[0] for result in tool_results]
    unique_dataset_keys = set(raw_dataset_keys)
    distinct_dates = {
        str(result.get("applied_params", {}).get("date", ""))
        for result in tool_results
        if result.get("applied_params", {}).get("date")
    }
    return len(unique_dataset_keys) == 1 and len(tool_results) > 1 and len(distinct_dates) > 1


def is_probable_dimension_column(column_name: str) -> bool:
    if column_name in KNOWN_DIMENSION_COLUMNS:
        return True
    if column_name in LIKELY_METRIC_COLUMNS:
        return False
    if re.search(r"[가-힣]", column_name):
        return True
    if column_name.isupper():
        return True
    if column_name.endswith("_NO") or column_name.endswith("_ID"):
        return True
    return False


def resolve_requested_dimensions(user_input: str, frames: List[pd.DataFrame]) -> List[str]:
    all_columns: List[str] = []
    for frame in frames:
        for column in frame.columns:
            if column not in all_columns:
                all_columns.append(str(column))
    return find_requested_dimensions(user_input, all_columns)


def pick_join_columns(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    requested_dimensions: List[str],
    exclude_date: bool,
) -> List[str]:
    shared_columns = set(left_df.columns) & set(right_df.columns)
    if exclude_date:
        shared_columns -= DATE_COLUMNS

    requested_join_columns = [column for column in requested_dimensions if column in shared_columns]
    preferred_columns = [column for column in KNOWN_DIMENSION_COLUMNS if column in shared_columns]
    extra_shared_dimensions = sorted(
        column
        for column in shared_columns
        if column not in requested_join_columns
        and column not in preferred_columns
        and is_probable_dimension_column(str(column))
    )

    join_columns = [*requested_join_columns]
    for column in [*preferred_columns, *extra_shared_dimensions]:
        if column not in join_columns:
            join_columns.append(column)
    return join_columns


def classify_join_cardinality(left_df: pd.DataFrame, right_df: pd.DataFrame, join_columns: List[str]) -> str:
    if not join_columns:
        return "unknown"
    left_unique = not left_df.duplicated(subset=join_columns).any()
    right_unique = not right_df.duplicated(subset=join_columns).any()
    if left_unique and right_unique:
        return "one_to_one"
    if left_unique and not right_unique:
        return "one_to_many"
    if not left_unique and right_unique:
        return "many_to_one"
    return "many_to_many"


def refine_join_columns_for_cardinality(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    join_columns: List[str],
    requested_dimensions: List[str],
    exclude_date: bool,
) -> tuple[List[str], str, List[str]]:
    current_columns = list(join_columns)
    current_cardinality = classify_join_cardinality(left_df, right_df, current_columns)
    if current_cardinality != "many_to_many":
        return current_columns, current_cardinality, []

    refined_with: List[str] = []
    all_candidates = pick_join_columns(left_df, right_df, requested_dimensions, exclude_date)
    extra_candidates = [column for column in all_candidates if column not in current_columns]

    for candidate in extra_candidates:
        trial_columns = [*current_columns, candidate]
        trial_cardinality = classify_join_cardinality(left_df, right_df, trial_columns)
        current_columns = trial_columns
        refined_with.append(candidate)
        current_cardinality = trial_cardinality
        if current_cardinality != "many_to_many":
            break

    return current_columns, current_cardinality, refined_with


def find_join_rule(left_dataset: str, right_dataset: str) -> Dict[str, Any] | None:
    for rule in get_registered_join_rules():
        if (
            normalize_text(rule.get("base_dataset", "")) == normalize_text(left_dataset)
            and normalize_text(rule.get("join_dataset", "")) == normalize_text(right_dataset)
        ):
            return rule
    return None


def expand_join_rule_columns(
    rule_columns: List[str],
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    requested_dimensions: List[str],
    exclude_date: bool,
) -> List[str]:
    shared_columns = set(left_df.columns) & set(right_df.columns)
    expanded_columns = [column for column in rule_columns if column in shared_columns]

    if not exclude_date and "WORK_DT" in shared_columns and "WORK_DT" not in expanded_columns:
        expanded_columns.append("WORK_DT")

    for column in requested_dimensions:
        if column in shared_columns and column not in expanded_columns:
            expanded_columns.append(column)

    return expanded_columns


def select_default_join_type(
    user_input: str,
    tool_results: List[Dict[str, Any]],
    left_dataset: str,
    right_dataset: str,
) -> str:
    normalized_query = normalize_text(user_input)

    if should_exclude_date_from_join(tool_results):
        return "outer"
    if any(token in normalized_query for token in ["鍮꾧탳", "李⑥씠", "?녿뒗", "紐⑸줉"]):
        return "left"

    selected_dataset_keys = {raw_dataset_key(result.get("dataset_key", "")) for result in tool_results}
    for rule in match_registered_analysis_rules(user_input):
        required = set(rule.get("required_datasets", []))
        if len(required) >= 2 and required.issubset(selected_dataset_keys):
            return "inner"

    if {left_dataset, right_dataset} <= {"production", "target"}:
        return "inner"
    return "outer"


def plan_merge_strategy(tool_results: List[Dict[str, Any]], frames: List[pd.DataFrame], user_input: str) -> Dict[str, Any]:
    exclude_date = should_exclude_date_from_join(tool_results)
    requested_dimensions = resolve_requested_dimensions(user_input, frames)
    base_index = 0

    join_rules = get_registered_join_rules()
    for index, result in enumerate(tool_results):
        dataset_key = raw_dataset_key(result.get("dataset_key", ""))
        if any(normalize_text(rule.get("base_dataset", "")) == normalize_text(dataset_key) for rule in join_rules):
            base_index = index
            break

    steps: List[Dict[str, Any]] = []
    base_dataset = raw_dataset_key(tool_results[base_index].get("dataset_key", ""))
    for index, result in enumerate(tool_results):
        if index == base_index:
            continue

        right_dataset = raw_dataset_key(result.get("dataset_key", ""))
        rule = find_join_rule(base_dataset, right_dataset)
        if rule:
            rule_join_columns = [
                column
                for column in rule.get("join_keys", [])
                if column in frames[base_index].columns and column in frames[index].columns
            ]
            join_columns = expand_join_rule_columns(
                rule_join_columns,
                frames[base_index],
                frames[index],
                requested_dimensions,
                exclude_date,
            )
            how = rule.get("join_type", "left")
            if not join_columns:
                join_columns = pick_join_columns(frames[base_index], frames[index], requested_dimensions, exclude_date)
        else:
            join_columns = pick_join_columns(frames[base_index], frames[index], requested_dimensions, exclude_date)
            how = select_default_join_type(user_input, tool_results, base_dataset, right_dataset)

        steps.append(
            {
                "right_index": index,
                "join_columns": join_columns,
                "how": how,
                "rule_name": rule.get("name", "") if rule else "",
                "left_dataset": base_dataset,
                "right_dataset": right_dataset,
            }
        )

    return {"base_index": base_index, "requested_dimensions": requested_dimensions, "steps": steps}


def cleanup_duplicate_dimension_columns(merged_df: pd.DataFrame) -> pd.DataFrame:
    columns_to_drop: List[str] = []
    for column in list(merged_df.columns):
        if not column.endswith("_x"):
            continue

        base_name = column[:-2]
        sibling = f"{base_name}_y"
        if sibling not in merged_df.columns or not is_probable_dimension_column(base_name):
            continue

        merged_df[base_name] = merged_df[column].where(merged_df[column].notna(), merged_df[sibling])
        columns_to_drop.extend([column, sibling])

    if columns_to_drop:
        merged_df = merged_df.drop(columns=list(dict.fromkeys(columns_to_drop)), errors="ignore")
    return merged_df


def merge_and_cleanup(
    merged_df: pd.DataFrame,
    next_df: pd.DataFrame,
    join_columns: List[str],
    how: str,
) -> tuple[pd.DataFrame, str]:
    cardinality = classify_join_cardinality(merged_df, next_df, join_columns)
    validate_map = {
        "one_to_one": "one_to_one",
        "one_to_many": "one_to_many",
        "many_to_one": "many_to_one",
    }

    merge_kwargs: Dict[str, Any] = {"on": join_columns, "how": how}
    if cardinality in validate_map:
        merge_kwargs["validate"] = validate_map[cardinality]

    merged = merged_df.merge(next_df, **merge_kwargs)
    merged = cleanup_duplicate_dimension_columns(merged)
    return merged, cardinality


def build_analysis_base_table(tool_results: List[Dict[str, Any]], user_input: str) -> Dict[str, Any]:
    prepared_frames: List[pd.DataFrame] = []
    source_names: List[str] = []
    suffix_metrics = should_suffix_metrics(tool_results)

    for result in tool_results:
        rows = result.get("data", [])
        if not isinstance(rows, list) or not rows:
            continue

        frame = pd.DataFrame(rows)
        available_dimensions = [column for column in frame.columns if is_probable_dimension_column(str(column))]
        metric_columns = [column for column in frame.columns if column not in available_dimensions]
        if not available_dimensions or not metric_columns:
            continue

        if suffix_metrics:
            source_tag = str(result.get("source_tag") or "source")
            rename_map = {column: f"{column}_{source_tag}" for column in metric_columns}
            frame = frame.rename(columns=rename_map)

        prepared_frames.append(frame.copy())
        source_names.append(str(result.get("result_label") or result.get("dataset_label") or result.get("tool_name", "unknown")))

    if not prepared_frames:
        return {
            "success": False,
            "tool_name": "analysis_base_table",
            "error_message": "遺꾩꽍??湲곗큹 ?뚯씠釉붿쓣 留뚮뱾 ???덈뒗 議고쉶 寃곌낵媛 ?놁뒿?덈떎.",
            "data": [],
        }

    merge_plan = plan_merge_strategy(tool_results, prepared_frames, user_input)
    if not merge_plan.get("steps"):
        return {
            "success": False,
            "tool_name": "analysis_base_table",
            "error_message": "?щ윭 ?곗씠?곕? 寃고빀??怨듯넻 湲곗???李얠? 紐삵뻽?듬땲??",
            "data": [],
        }

    merged_df = prepared_frames[merge_plan["base_index"]]
    applied_join_columns: List[str] = []
    merge_notes: List[str] = []
    exclude_date = should_exclude_date_from_join(tool_results)

    for step in merge_plan["steps"]:
        next_df = prepared_frames[step["right_index"]]
        next_join_columns = [column for column in step["join_columns"] if column in next_df.columns and column in merged_df.columns]
        if not next_join_columns:
            return {
                "success": False,
                "tool_name": "analysis_base_table",
                "error_message": "?щ윭 ?곗씠?곕? 寃고빀??怨듯넻 湲곗???李얠? 紐삵뻽?듬땲??",
                "data": [],
            }

        refined_join_columns, cardinality, refined_with = refine_join_columns_for_cardinality(
            merged_df,
            next_df,
            next_join_columns,
            merge_plan.get("requested_dimensions", []),
            exclude_date,
        )
        if cardinality == "many_to_many":
            join_preview = ", ".join(next_join_columns)
            tried_preview = ", ".join(refined_join_columns)
            return {
                "success": False,
                "tool_name": "analysis_base_table",
                "error_message": (
                    "怨듯넻 寃고빀 湲곗???異⑸텇?섏? ?딆븘 ?덉쟾?섍쾶 蹂묓빀?????놁뒿?덈떎. "
                    f"`{step['left_dataset']}`? `{step['right_dataset']}`瑜??⑹튂湲??꾪빐 "
                    f"`{join_preview}` 湲곗???癒쇱? ?쒕룄?덇퀬, "
                    f"`{tried_preview}`源뚯? ?뺤옣?덉?留??ъ쟾??N:M 愿怨꾩??듬땲??"
                ),
                "data": [],
            }

        merged_df, cardinality = merge_and_cleanup(merged_df, next_df, refined_join_columns, step["how"])
        for column in refined_join_columns:
            if column not in applied_join_columns:
                applied_join_columns.append(column)
        merge_note = (
            f"{step['left_dataset']} -> {step['right_dataset']} "
            f"({step['how']}, {cardinality}, keys={', '.join(refined_join_columns)})"
        )
        if refined_with:
            merge_note += f", refined_with={', '.join(refined_with)}"
        if step.get("rule_name"):
            merge_note += f", rule={step['rule_name']}"
        merge_notes.append(merge_note)

    merged_df = merged_df.where(pd.notnull(merged_df), None)
    return {
        "success": True,
        "tool_name": "analysis_base_table",
        "data": merged_df.to_dict(orient="records"),
        "summary": f"蹂듭닔 ?곗씠?곗뀑 蹂묓빀 寃곌낵: {', '.join(source_names)}, 珥?{len(merged_df)}嫄?",
        "source_tool_names": source_names,
        "join_columns": applied_join_columns,
        "merge_notes": merge_notes,
        "requested_dimensions": merge_plan.get("requested_dimensions", []),
    }


def build_multi_dataset_overview(tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    overview_rows = []
    for result in tool_results:
        overview_rows.append(
            {
                "?곗씠?곗뀑": result.get("dataset_label", result.get("dataset_key", "")),
                "?됱닔": len(result.get("data", [])) if isinstance(result.get("data"), list) else 0,
                "?붿빟": result.get("summary", ""),
            }
        )

    return {
        "success": True,
        "tool_name": "multi_dataset_overview",
        "data": overview_rows,
        "summary": f"蹂듭닔 ?곗씠?곗뀑 議고쉶 ?꾨즺: 珥?{len(overview_rows)}媛?",
    }
