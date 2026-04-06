"""Streamlit page for user-managed domain registry entries."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from ..domain.registry import (
    delete_domain_entry,
    get_domain_registry_summary,
    list_domain_entries,
    preview_domain_submission,
    register_domain_submission,
)


def _format_table(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _render_issue_messages(issues: List[Dict[str, str]]) -> None:
    for issue in issues:
        severity = issue.get("severity", "info")
        message = issue.get("message", "")
        if severity == "error":
            st.error(message)
        elif severity == "warning":
            st.warning(message)
        else:
            st.info(message)


def _render_payload_section(title: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    st.markdown(f"**{title}**")
    st.dataframe(_format_table(rows), width="stretch", hide_index=True)


def _render_preview(preview: Dict[str, Any]) -> None:
    payload = preview.get("payload", {})
    issues = preview.get("issues", [])

    st.markdown("**Preview**")
    st.write(f"Title: {payload.get('title', '')}")
    if issues:
        _render_issue_messages(issues)
    else:
        st.success("This note looks valid and can be saved.")

    _render_payload_section("Dataset keywords", payload.get("dataset_keywords", []))
    _render_payload_section("Value groups", payload.get("value_groups", []))
    _render_payload_section("Analysis rules", payload.get("analysis_rules", []))
    _render_payload_section("Join rules", payload.get("join_rules", []))

    if payload.get("notes"):
        st.markdown("**Notes**")
        for note in payload["notes"]:
            st.markdown(f"- {note}")


def render_domain_registry_summary_card() -> None:
    summary = get_domain_registry_summary()
    if not summary["custom_entry_count"]:
        return

    st.info(
        "Custom domain registry | "
        f"entries {summary['custom_entry_count']} / "
        f"value groups {summary['custom_value_group_count']} / "
        f"analysis rules {summary['custom_analysis_rule_count']} / "
        f"join rules {summary['custom_join_rule_count']}"
    )


def _render_summary_cards(summary: Dict[str, Any]) -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.metric("Builtin value groups", summary["builtin_value_group_count"])
            st.caption("Static process/mode/pkg groups from the codebase.")
    with col2:
        with st.container(border=True):
            st.metric("Builtin analysis rules", summary["builtin_analysis_rule_count"])
            st.caption("Built-in derived metric rules such as achievement rate.")
    with col3:
        with st.container(border=True):
            st.metric("Custom entries", summary["custom_entry_count"])
            st.caption("User-saved domain notes that extend the assistant.")


def _render_entry_list() -> None:
    entries = list_domain_entries()
    st.markdown("### Saved Entries")
    if not entries:
        st.caption("No custom domain entries yet.")
        return

    for entry in entries:
        title = str(entry.get("title", "untitled"))
        created_at = str(entry.get("created_at", ""))
        with st.expander(f"{title} | {created_at}", expanded=False):
            st.code(str(entry.get("raw_text", "")))
            _render_payload_section("Dataset keywords", entry.get("dataset_keywords", []))
            _render_payload_section("Value groups", entry.get("value_groups", []))
            _render_payload_section("Analysis rules", entry.get("analysis_rules", []))
            _render_payload_section("Join rules", entry.get("join_rules", []))

            if st.button(f"Delete {entry.get('id')}", key=f"delete_{entry.get('id')}"):
                deleted = delete_domain_entry(str(entry.get("id", "")))
                if deleted.get("success"):
                    st.success(deleted.get("message", "Deleted"))
                    st.rerun()
                st.error(deleted.get("message", "Delete failed"))


def render_domain_knowledge_page() -> None:
    st.title("Domain Registry")
    st.caption("Save manufacturing notes as structured dataset keywords, value groups, analysis rules, and join rules.")

    summary = get_domain_registry_summary()
    _render_summary_cards(summary)
    render_domain_registry_summary_card()

    st.markdown("### Add Domain Note")
    default_text = (
        "Example:\n"
        "- '조립공정' means D/A1 and D/A2.\n"
        "- Hold load index is hold_qty / production.\n"
        "- production and target should join on WORK_DT, OPER_NAME, MODE."
    )
    raw_text = st.text_area("Write a manufacturing rule or note", height=220, value=default_text)

    preview_col, save_col = st.columns(2)
    preview = None

    with preview_col:
        if st.button("Preview", use_container_width=True):
            preview = preview_domain_submission(raw_text)
            st.session_state.domain_preview = preview

    if preview is None:
        preview = st.session_state.get("domain_preview")

    if preview:
        _render_preview(preview)

    with save_col:
        can_save = bool(preview and preview.get("can_save"))
        if st.button("Save", use_container_width=True, disabled=not can_save):
            saved = register_domain_submission(raw_text)
            if saved.get("success"):
                st.success(saved.get("message", "Saved"))
                st.session_state.domain_preview = None
                st.rerun()
            else:
                st.error(saved.get("message", "Save failed"))
                _render_issue_messages(saved.get("issues", []))

    st.divider()
    _render_entry_list()
