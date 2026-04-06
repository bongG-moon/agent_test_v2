"""Streamlit rendering helpers for chat results and session state."""

from typing import Any, Dict, List, MutableMapping, Set

import pandas as pd
import streamlit as st

from ..shared.number_format import format_rows_for_display


def empty_context() -> Dict[str, Any]:
    return {
        "date": None,
        "process_name": None,
        "oper_num": None,
        "pkg_type1": None,
        "pkg_type2": None,
        "product_name": None,
        "line_name": None,
        "mode": None,
        "den": None,
        "tech": None,
        "lead": None,
        "mcp_no": None,
    }


def has_active_context(context: Dict[str, Any] | None) -> bool:
    current = context or {}
    return any(value not in (None, "", []) for value in current.values())


def reset_filter_context(state: MutableMapping[str, Any]) -> None:
    state["context"] = empty_context()


def reset_filter_session(state: MutableMapping[str, Any]) -> None:
    state["current_data"] = None
    reset_filter_context(state)


def reset_chat_session(state: MutableMapping[str, Any]) -> None:
    state["messages"] = []
    reset_filter_session(state)


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_data" not in st.session_state:
        st.session_state.current_data = None
    if "context" not in st.session_state:
        st.session_state.context = empty_context()
    if "engineer_mode" not in st.session_state:
        st.session_state.engineer_mode = False


def format_display_dataframe(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    formatted_rows, _ = format_rows_for_display(rows)
    return pd.DataFrame(formatted_rows)


def _build_analysis_logic_labels(analysis_logic: str) -> tuple[str, str]:
    logic = str(analysis_logic or "").strip().lower()
    label_map = {
        "llm_primary": "LLM generated pandas code directly.",
        "llm_retry": "LLM retried with corrected pandas code.",
        "minimal_fallback": "A minimal fallback sort/filter path was used.",
        "domain_rule_fallback": "A registered domain rule was used as fallback.",
    }
    description_map = {
        "llm_primary": "This is the normal path when the requested transformation is understood clearly.",
        "llm_retry": "The first generated code was not good enough, so the model corrected it once.",
        "minimal_fallback": "A simple fallback was used because a richer analysis plan was unavailable.",
        "domain_rule_fallback": "A registered calculation rule was used to keep the result stable.",
    }
    return label_map.get(logic, ""), description_map.get(logic, "")


def render_applied_params(applied_params: Dict[str, Any]) -> None:
    label_map = {
        "date": "Date",
        "process_name": "Process",
        "oper_num": "Oper No",
        "pkg_type1": "PKG TYPE1",
        "pkg_type2": "PKG TYPE2",
        "product_name": "Product",
        "line_name": "Line",
        "mode": "MODE",
        "den": "DEN",
        "tech": "TECH",
        "lead": "LEAD",
        "mcp_no": "MCP",
        "group_by": "Group By",
    }
    for key, value in applied_params.items():
        if value in (None, "", []):
            continue
        rendered = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value)
        st.markdown(f"- **{label_map.get(key, key)}**: {rendered}")


def render_context() -> None:
    context = st.session_state.get("context", {})
    active = []
    label_map = [
        ("date", "Date"),
        ("process_name", "Process"),
        ("oper_num", "Oper No"),
        ("pkg_type1", "PKG TYPE1"),
        ("pkg_type2", "PKG TYPE2"),
        ("product_name", "Product"),
        ("line_name", "Line"),
        ("mode", "MODE"),
        ("den", "DEN"),
        ("tech", "TECH"),
        ("lead", "LEAD"),
        ("mcp_no", "MCP"),
    ]
    for field, label in label_map:
        value = context.get(field)
        if value:
            rendered = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value)
            active.append(f"{label}: {rendered}")
    if active:
        st.info("Current query context | " + " / ".join(active))


def render_analysis_summary(result: Dict[str, Any], row_count: int) -> None:
    analysis_plan = result.get("analysis_plan", {})
    transformation_summary = result.get("transformation_summary", {})
    source_label, source_description = _build_analysis_logic_labels(result.get("analysis_logic", ""))

    st.markdown("**Analysis Summary**")
    if source_label:
        st.markdown(f"- **Execution path**: {source_label}")
    if source_description:
        st.caption(source_description)
    if analysis_plan.get("intent"):
        st.markdown(f"- **Intent**: {analysis_plan.get('intent')}")
    if transformation_summary.get("group_by_columns"):
        st.markdown(f"- **Group by**: {', '.join(transformation_summary.get('group_by_columns', []))}")
    if transformation_summary.get("metric_column"):
        st.markdown(f"- **Metric**: {transformation_summary.get('metric_column')}")
    if transformation_summary.get("sort_by"):
        st.markdown(f"- **Sort**: {transformation_summary.get('sort_by')} ({transformation_summary.get('sort_order', 'desc')})")
    if transformation_summary.get("top_n"):
        st.markdown(f"- **Top N**: {transformation_summary.get('top_n')}")
    if transformation_summary.get("top_n_per_group"):
        st.markdown(f"- **Top N per group**: {transformation_summary.get('top_n_per_group')}")
    if transformation_summary.get("input_row_count") is not None:
        st.markdown(
            f"- **Row change**: {transformation_summary.get('input_row_count')} -> "
            f"{transformation_summary.get('output_row_count', row_count)}"
        )
    st.markdown(f"- **Output rows**: {row_count}")

    analysis_base_info = result.get("analysis_base_info", {})
    if analysis_base_info.get("source_tool_names"):
        st.markdown(f"- **Merged sources**: {', '.join(analysis_base_info.get('source_tool_names', []))}")
    if analysis_base_info.get("join_columns"):
        st.markdown(f"- **Join columns**: {', '.join(analysis_base_info.get('join_columns', []))}")


def _get_expanded_indexes(tool_results: List[Dict[str, Any]]) -> Set[int]:
    expanded_indexes = {
        index
        for index, result in enumerate(tool_results)
        if result.get("success") and result.get("display_expanded") is True
    }
    if expanded_indexes:
        return expanded_indexes

    for index in range(len(tool_results) - 1, -1, -1):
        if tool_results[index].get("success"):
            return {index}
    return set()


def _build_result_title(result: Dict[str, Any]) -> str:
    tool_name = str(result.get("tool_name", "result"))
    summary = str(result.get("summary", "")).strip()
    return f"{tool_name} | {summary}" if summary else tool_name


def render_tool_results(tool_results: List[Dict[str, Any]], engineer_mode: bool = False) -> None:
    expanded_indexes = _get_expanded_indexes(tool_results)

    for index, result in enumerate(tool_results):
        if not result.get("success"):
            st.error(result.get("error_message", "An error occurred."))
            continue

        title = _build_result_title(result)
        with st.expander(title, expanded=index in expanded_indexes):
            data = result.get("data", [])
            if data:
                st.dataframe(format_display_dataframe(data), width="stretch", hide_index=True)
            else:
                st.caption("No rows to display.")

            applied_params = result.get("applied_params", {})
            if applied_params:
                st.markdown("**Applied Filters**")
                render_applied_params(applied_params)

            if engineer_mode and result.get("tool_name") == "analyze_current_data":
                render_analysis_summary(result, len(data))
                generated_code = str(result.get("generated_code", "")).strip()
                if generated_code:
                    st.markdown("**Generated pandas code**")
                    st.code(generated_code, language="python")


def sync_context(extracted_params: Dict[str, Any]) -> None:
    for field in [
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
    ]:
        value = extracted_params.get(field)
        if value:
            st.session_state.context[field] = value
