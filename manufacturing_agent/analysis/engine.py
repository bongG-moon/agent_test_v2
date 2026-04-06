"""Run follow-up analysis against an already retrieved table."""

from typing import Any, Dict, List

from .helpers import (
    build_transformation_summary,
    extract_columns,
    find_missing_dimensions,
    find_requested_dimensions,
    format_missing_column_message,
    minimal_fallback_plan,
    validate_plan_columns,
)
from .llm_planner import build_llm_plan
from .safe_executor import execute_safe_dataframe_code
from ..domain.registry import match_registered_analysis_rules


def _find_semantic_retry_reason(query_text: str, columns: List[str], code: str) -> str:
    query = str(query_text or "")
    code_text = str(code or "")
    available = set(columns)
    lower_query = query.lower()

    if "hold_reason" in available and ("hold reason" in lower_query or "대표 hold 사유" in query):
        if "hold_reason" not in code_text:
            return "The previous code did not use `hold_reason` even though the user asked for it."

    if "avg_wait_minutes" in available and "상태" in available and ("hold lot" in lower_query or "대기시간" in query):
        has_wait_metric = "avg_wait_minutes" in code_text
        has_hold_count = "HOLD" in code_text or "hold_lot" in code_text or "상태" in code_text
        if not (has_wait_metric and has_hold_count):
            return "The previous code did not include both average wait time and hold lot count."

    if "production" in available and "target" in available and (
        "achievement" in lower_query or "달성" in query or "목표" in query
    ):
        has_production = "production" in code_text
        has_target = "target" in code_text
        has_ratio = "/" in code_text or "achievement" in code_text.lower()
        if not (has_production and has_target and has_ratio):
            return "The previous code did not calculate achievement rate from both `production` and `target`."

    if ("missing" in lower_query or "list" in lower_query or "없는" in query or "목록" in query) and not any(
        token in code_text for token in ["isna(", "isnull(", "notna(", "notnull("]
    ):
        return "The previous code did not apply missing-value filtering even though the user asked for missing rows."

    return ""


def _execute_plan(plan: Dict[str, Any], data: List[Dict[str, Any]]) -> Dict[str, Any]:
    return execute_safe_dataframe_code(str(plan.get("code", "")).strip(), data)


def _pick_ratio_operands(rule: Dict[str, Any], columns: List[str]) -> tuple[str | None, str | None]:
    role_map: Dict[str, str] = {}
    ordered_columns: List[str] = []

    for item in rule.get("source_columns", []):
        column_name = str(item.get("column", "")).strip()
        if not column_name or column_name not in columns:
            continue
        ordered_columns.append(column_name)
        role_name = str(item.get("role", "")).strip().lower()
        if role_name:
            role_map[role_name] = column_name

    numerator = role_map.get("numerator") or role_map.get("left") or role_map.get("base") or (ordered_columns[0] if ordered_columns else None)
    denominator = (
        role_map.get("denominator")
        or role_map.get("right")
        or role_map.get("compare")
        or (ordered_columns[1] if len(ordered_columns) > 1 else None)
    )

    if numerator and denominator:
        return numerator, denominator

    available_required = [column for column in rule.get("required_columns", []) if column in columns]
    if len(available_required) >= 2:
        return available_required[0], available_required[1]

    return numerator, denominator


def _pick_group_columns(query_text: str, columns: List[str], matched_rules: List[Dict[str, Any]]) -> List[str]:
    explicit_group_columns = [column for column in find_requested_dimensions(query_text, columns) if column in columns]
    if explicit_group_columns:
        return explicit_group_columns

    default_group_columns: List[str] = []
    for rule in matched_rules:
        for column in rule.get("default_group_by", []):
            if column in columns and column not in default_group_columns:
                default_group_columns.append(column)
    if default_group_columns:
        return default_group_columns

    for candidate in ["OPER_NAME", "FAMILY", "MODE", "DEN", "TECH", "LEAD", "WORK_DT"]:
        if candidate in columns:
            return [candidate]
    return []


def _build_domain_rule_fallback_plan(query_text: str, data: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    columns = extract_columns(data)
    matched_rules = match_registered_analysis_rules(query_text)
    if not matched_rules:
        return None

    ratio_rules = []
    for rule in matched_rules:
        if str(rule.get("calculation_mode", "")).strip() != "ratio":
            continue
        numerator, denominator = _pick_ratio_operands(rule, columns)
        output_column = str(rule.get("output_column", "")).strip() or str(rule.get("name", "")).strip()
        if numerator and denominator and output_column:
            ratio_rules.append(
                {
                    "output_column": output_column,
                    "numerator": numerator,
                    "denominator": denominator,
                }
            )

    if not ratio_rules:
        return None

    group_columns = _pick_group_columns(query_text, columns, matched_rules)
    output_columns = [*group_columns, *[item["output_column"] for item in ratio_rules]]

    aggregate_columns: List[str] = []
    for item in ratio_rules:
        for column_name in [item["numerator"], item["denominator"]]:
            if column_name not in aggregate_columns:
                aggregate_columns.append(column_name)

    helper_names = {column_name: f"__sum_{index}" for index, column_name in enumerate(aggregate_columns, start=1)}
    agg_lines = [f"    {helper_names[column_name]}=({column_name!r}, 'sum')" for column_name in aggregate_columns]

    code_lines: List[str] = []
    if group_columns:
        code_lines.append(f"grouped = df.groupby({group_columns!r}, as_index=False).agg(\n" + ",\n".join(agg_lines) + "\n)")
    else:
        overall_items = ", ".join(f"{helper_names[column_name]!r}: [df[{column_name!r}].sum()]" for column_name in aggregate_columns)
        code_lines.append(f"grouped = pd.DataFrame({{{overall_items}}})")

    for item in ratio_rules:
        numerator_name = helper_names[item["numerator"]]
        denominator_name = helper_names[item["denominator"]]
        code_lines.append(f"grouped[{item['output_column']!r}] = grouped[{numerator_name!r}] / grouped[{denominator_name!r}]")

    code_lines.append(f"result = grouped[{output_columns!r}]")

    return {
        "intent": "registered domain-rule fallback",
        "operations": ["groupby", "agg", "derived_metric"] if group_columns else ["agg", "derived_metric"],
        "output_columns": output_columns,
        "group_by_columns": group_columns,
        "partition_by_columns": [],
        "filters": [],
        "sort_by": "",
        "sort_order": "desc",
        "metric_column": ratio_rules[0]["output_column"],
        "warnings": ["Domain rule fallback was used because the LLM plan was missing or unsafe."],
        "code": "\n".join(code_lines),
        "source": "domain_rule_fallback",
    }


def _success_result(
    plan: Dict[str, Any],
    analysis_logic: str,
    result_rows: List[Dict[str, Any]],
    source_tool_name: str,
    input_rows: int,
) -> Dict[str, Any]:
    return {
        "success": True,
        "tool_name": "analyze_current_data",
        "data": result_rows,
        "summary": f"Current-data analysis complete: {len(result_rows)} rows",
        "analysis_plan": plan,
        "analysis_logic": analysis_logic,
        "generated_code": plan.get("code", ""),
        "source_tool_name": source_tool_name,
        "transformation_summary": build_transformation_summary(
            plan,
            input_rows=input_rows,
            output_rows=len(result_rows),
            analysis_logic=analysis_logic,
        ),
    }


def _error_result(
    error_message: str,
    columns: List[str],
    plan: Dict[str, Any] | None = None,
    analysis_logic: str | None = None,
    missing_columns: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "success": False,
        "tool_name": "analyze_current_data",
        "error_message": error_message,
        "data": [],
        "analysis_plan": plan,
        "analysis_logic": analysis_logic,
        "generated_code": (plan or {}).get("code", ""),
        "missing_columns": missing_columns or [],
        "available_columns": columns,
    }


def _execute_with_retry(query_text: str, data: List[Dict[str, Any]], plan: Dict[str, Any], analysis_logic: str):
    executed = _execute_plan(plan, data)
    if executed.get("success") or str(plan.get("source")) != "llm_primary":
        return executed, plan, analysis_logic

    retry_plan, retry_logic = build_llm_plan(
        query_text,
        data,
        retry_error=str(executed.get("error_message", "")),
        previous_code=str(plan.get("code", "")),
    )
    if retry_plan is None:
        return executed, plan, analysis_logic

    retry_executed = _execute_plan(retry_plan, data)
    return retry_executed, retry_plan, retry_logic


def execute_analysis_query(query_text: str, data: List[Dict[str, Any]], source_tool_name: str = "") -> Dict[str, Any]:
    if not data:
        return {
            "success": False,
            "tool_name": "analyze_current_data",
            "error_message": "There is no current table to analyze.",
            "data": [],
        }

    columns = extract_columns(data)
    missing_dimensions = find_missing_dimensions(query_text, columns)
    if missing_dimensions:
        return _error_result(
            format_missing_column_message(missing_dimensions, columns),
            columns,
            missing_columns=missing_dimensions,
        )

    domain_rule_plan = _build_domain_rule_fallback_plan(query_text, data)

    plan, analysis_logic = build_llm_plan(query_text, data)
    if plan is None:
        if domain_rule_plan is not None:
            plan = domain_rule_plan
            analysis_logic = "domain_rule_fallback"
        else:
            plan = minimal_fallback_plan(query_text, data)
            analysis_logic = "minimal_fallback"
    else:
        semantic_retry_reason = _find_semantic_retry_reason(query_text, columns, str(plan.get("code", "")))
        if semantic_retry_reason:
            retry_plan, retry_logic = build_llm_plan(
                query_text,
                data,
                retry_error=semantic_retry_reason,
                previous_code=str(plan.get("code", "")),
            )
            if retry_plan is not None:
                plan = retry_plan
                analysis_logic = retry_logic

    plan_missing_columns = validate_plan_columns(plan, columns)
    if plan_missing_columns and domain_rule_plan is not None and analysis_logic != "domain_rule_fallback":
        plan = domain_rule_plan
        analysis_logic = "domain_rule_fallback"
        plan_missing_columns = validate_plan_columns(plan, columns)

    if plan_missing_columns:
        return _error_result(
            format_missing_column_message(plan_missing_columns, columns),
            columns,
            plan=plan,
            analysis_logic=analysis_logic,
            missing_columns=plan_missing_columns,
        )

    executed, final_plan, final_logic = _execute_with_retry(query_text, data, plan, analysis_logic)
    if not executed.get("success") and domain_rule_plan is not None and final_logic != "domain_rule_fallback":
        executed = _execute_plan(domain_rule_plan, data)
        final_plan = domain_rule_plan
        final_logic = "domain_rule_fallback"

    if not executed.get("success"):
        error_message = str(executed.get("error_message", "Analysis code execution failed."))
        if "KeyError" in error_message:
            missing_from_error = plan_missing_columns or missing_dimensions or ["requested column"]
            error_message = format_missing_column_message(missing_from_error, columns)

        return _error_result(
            error_message,
            columns,
            plan=final_plan,
            analysis_logic=final_logic,
            missing_columns=plan_missing_columns,
        )

    result_rows = executed.get("data", [])
    return _success_result(final_plan, final_logic, result_rows, source_tool_name, len(data))
