import json
import importlib.util
import threading
import time
from pathlib import Path

import pytest

from langflow_version.components import ManufacturingAgentComponent
from langflow_version.workflow import build_initial_state, resolve_request_step, run_langflow_workflow
from manufacturing_agent.agent import extract_params_component, run_agent, run_agent_with_progress
from manufacturing_agent.data import retrieval as retrieval_data
from manufacturing_agent.data.retrieval import get_production_data
from manufacturing_agent.domain import registry
from manufacturing_agent.app.ui_renderer import build_retry_question_suggestions
from manufacturing_agent.services import parameter_service, request_context, response_service, retrieval_planner
from manufacturing_agent.services.merge_service import build_analysis_base_table
from manufacturing_agent.services.query_mode import (
    choose_query_mode,
    has_explicit_date_reference,
    mentions_grouping_expression,
)
from manufacturing_agent.services.runtime_service import ensure_filtered_result_rows
from manufacturing_agent.shared.column_resolver import normalize_dataset_result_columns
from manufacturing_agent.shared.text_sanitizer import sanitize_markdown_text


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeLLM:
    def __init__(self, content):
        self._content = content

    def invoke(self, _messages):
        return _FakeResponse(self._content)


def _stub_llms(monkeypatch, content="{}"):
    monkeypatch.setattr(parameter_service, "get_llm", lambda *args, **kwargs: _FakeLLM(content))
    monkeypatch.setattr(request_context, "get_llm", lambda *args, **kwargs: _FakeLLM(content))


def _stub_retrieval_planner_llm(monkeypatch, payload):
    monkeypatch.setattr(
        retrieval_planner,
        "get_llm_for_task",
        lambda *_args, **_kwargs: _FakeLLM(json.dumps(payload, ensure_ascii=False)),
    )


def test_project_has_beginner_friendly_package_layout():
    root = Path(__file__).resolve().parents[1]
    assert (root / "manufacturing_agent" / "graph").exists()
    assert (root / "manufacturing_agent" / "services").exists()
    assert (root / "manufacturing_agent" / "domain").exists()
    assert (root / "manufacturing_agent" / "agent.py").exists()


def test_expand_registered_process_group_uses_builtin_domain_values():
    expanded = registry.expand_registered_values("process_name", ["DA"])
    assert expanded is not None
    assert "D/A1" in expanded
    assert "D/A6" in expanded


def test_resolve_required_params_detects_process_and_mode_without_real_llm(monkeypatch):
    _stub_llms(monkeypatch)

    result = parameter_service.resolve_required_params(
        user_input="today DA process DDR5 production",
        chat_history_text="",
        current_data_columns=[],
        context={},
    )

    assert result["date"] is not None
    assert result["mode"] == ["DDR5"]
    assert "D/A1" in result["process_name"]


def test_resolve_required_params_detects_oper_num_with_domain_based_detector(monkeypatch):
    _stub_llms(monkeypatch)

    result = parameter_service.resolve_required_params(
        user_input="oper_num 2030 production",
        chat_history_text="",
        current_data_columns=[],
        context={},
    )

    assert result["oper_num"] == ["2030"]


def test_resolve_required_params_detects_pkg_value_without_field_specific_helper(monkeypatch):
    _stub_llms(monkeypatch)

    result = parameter_service.resolve_required_params(
        user_input="today FCBGA production",
        chat_history_text="",
        current_data_columns=[],
        context={},
    )

    assert result["pkg_type1"] == ["FCBGA"]


def test_resolve_required_params_normalizes_special_product_with_domain_rule(monkeypatch):
    _stub_llms(monkeypatch)

    result = parameter_service.resolve_required_params(
        user_input="오늘 HBM 제품 생산량 알려줘",
        chat_history_text="",
        current_data_columns=[],
        context={},
    )

    assert result["product_name"] == "HBM_OR_3DS"


def test_resolve_required_params_maps_input_keyword_to_process_with_domain_rule(monkeypatch):
    _stub_llms(monkeypatch)

    result = parameter_service.resolve_required_params(
        user_input="오늘 투입 생산량 알려줘",
        chat_history_text="",
        current_data_columns=[],
        context={},
    )

    assert result["process_name"] == ["INPUT"]


def test_choose_query_mode_keeps_followup_for_same_scope_transform():
    current_data = {
        "success": True,
        "tool_name": "get_production_data",
        "dataset_key": "production",
        "source_dataset_keys": ["production"],
        "applied_params": {"date": "20260404", "process_name": ["D/A1", "D/A2"]},
        "data": [
            {"WORK_DT": "20260404", "OPER_NAME": "D/A1", "MODE": "DDR5", "production": 100},
            {"WORK_DT": "20260404", "OPER_NAME": "D/A2", "MODE": "LPDDR5", "production": 120},
        ],
    }

    query_mode = choose_query_mode(
        "group by MODE",
        current_data,
        {"date": "20260404", "process_name": ["D/A1", "D/A2"], "group_by": "MODE"},
    )

    assert query_mode == "followup_transform"


def test_query_mode_signal_specs_drive_date_and_grouping_detection():
    assert has_explicit_date_reference("오늘 생산량 알려줘") is True
    assert mentions_grouping_expression("MODE별로 다시 보여줘") is True


def test_langflow_extract_params_component_returns_plain_dict(monkeypatch):
    _stub_llms(monkeypatch)

    result = extract_params_component(
        {
            "user_input": "today DA process DDR5 production",
            "chat_history": [],
            "current_data": None,
            "context": {},
        }
    )

    assert isinstance(result, dict)
    assert "extracted_params" in result
    assert result["extracted_params"]["mode"] == ["DDR5"]


def test_run_agent_smoke_returns_result_payload(monkeypatch):
    _stub_llms(monkeypatch)

    result = run_agent(
        user_input="today DA process DDR5 wip",
        chat_history=[],
        context={},
        current_data=None,
    )

    assert isinstance(result, dict)
    assert result["tool_results"]
    assert result["current_data"]["tool_name"] in {"get_wip_status", "multi_dataset_overview", "analyze_current_data"}


def test_langflow_workflow_reuses_same_core_logic(monkeypatch):
    _stub_llms(monkeypatch)

    state = build_initial_state(
        user_input="today DA process DDR5 production",
        chat_history=[],
        context={},
        current_data=None,
    )
    resolved = resolve_request_step(state)

    assert resolved["query_mode"] == "retrieval"
    assert "D/A1" in resolved["extracted_params"]["process_name"]


def test_langflow_full_workflow_returns_result_payload(monkeypatch):
    _stub_llms(monkeypatch)

    result = run_langflow_workflow(
        user_input="today DA process DDR5 wip",
        chat_history=[],
        context={},
        current_data=None,
    )

    assert isinstance(result, dict)
    assert result["tool_results"]
    assert result["execution_engine"] == "langflow_v2"


def test_langflow_component_module_imports_without_langflow_installed():
    assert ManufacturingAgentComponent.name == "manufacturing_agent_component"


def test_langflow_components_path_loader_imports_component_classes():
    if importlib.util.find_spec("lfx") is None:
        pytest.skip("lfx is not installed in this local test environment")

    loader_path = Path(__file__).resolve().parents[1] / "langflow_components" / "manufacturing_agent" / "manufacturing_agent_component.py"
    spec = importlib.util.spec_from_file_location("manufacturing_components_loader", loader_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert module.ManufacturingAgentComponent.name == "manufacturing_agent_component"


def test_langflow_components_path_builds_visible_custom_components():
    if importlib.util.find_spec("lfx") is None:
        pytest.skip("lfx is not installed in this local test environment")

    from lfx.custom.directory_reader.utils import build_custom_component_list_from_path

    path = Path(__file__).resolve().parents[1] / "langflow_components"
    component_dict = build_custom_component_list_from_path(str(path))

    assert "manufacturing_agent" in component_dict
    loaded_names = set(component_dict["manufacturing_agent"].keys())
    assert "manufacturing_agent_component" in loaded_names
    assert "resolve_manufacturing_request" in loaded_names


def test_build_retry_question_suggestions_recommends_grouped_retry_for_column_error():
    suggestions = build_retry_question_suggestions(
        "오늘 DA공정에서 DDR5제품의 생산 달성율을 공정별로 알려줘",
        "요청한 컬럼 OPER_NAME 을(를) 현재 테이블에서 찾을 수 없습니다.",
    )

    assert suggestions
    assert any("공정별" in item or "MODE별" in item for item in suggestions)


def test_build_retry_question_suggestions_uses_failure_type_for_unknown_dataset():
    suggestions = build_retry_question_suggestions(
        "이상한 질문",
        "무슨 데이터를 조회해야 할지 모르겠습니다.",
        failure_type="unknown_dataset",
    )

    assert suggestions
    assert any("생산량" in item or "목표" in item for item in suggestions)


def test_run_agent_with_progress_reports_real_steps(monkeypatch):
    _stub_llms(monkeypatch)

    progress_events = []

    result = run_agent_with_progress(
        user_input="today DA process DDR5 production",
        chat_history=[],
        context={},
        current_data=None,
        progress_callback=lambda title, detail: progress_events.append((title, detail)),
    )

    assert result["tool_results"]
    assert progress_events
    assert progress_events[0][0] == "1/3 파라미터 해석중"
    assert any(title == "2/3 데이터 조회중" for title, _detail in progress_events)


def test_execute_retrieval_jobs_reuses_cached_results(monkeypatch):
    params = {"date": "20260410", "process_name": ["D/A1"]}
    call_count = {"value": 0}

    def fake_execute_retrieval_tools(dataset_keys, job_params):
        call_count["value"] += 1
        return [
            {
                "success": True,
                "tool_name": f"get_{dataset_keys[0]}",
                "dataset_key": dataset_keys[0],
                "dataset_label": dataset_keys[0],
                "data": [{"WORK_DT": job_params["date"], "production": 100}],
                "summary": "ok",
            }
        ]

    retrieval_planner.RETRIEVAL_RESULT_CACHE.clear()
    monkeypatch.setattr(retrieval_planner, "execute_retrieval_tools", fake_execute_retrieval_tools)

    first = retrieval_planner.execute_retrieval_jobs([{"dataset_key": "production", "params": params, "result_label": None}])[0]
    second = retrieval_planner.execute_retrieval_jobs([{"dataset_key": "production", "params": params, "result_label": None}])[0]

    assert call_count["value"] == 1
    assert first["from_cache"] is False
    assert second["from_cache"] is True


def test_execute_retrieval_jobs_runs_multi_dataset_requests_in_parallel(monkeypatch):
    thread_ids = set()

    def fake_execute_retrieval_tools(dataset_keys, job_params):
        time.sleep(0.05)
        thread_ids.add(threading.get_ident())
        dataset_key = dataset_keys[0]
        return [
            {
                "success": True,
                "tool_name": f"get_{dataset_key}",
                "dataset_key": dataset_key,
                "dataset_label": dataset_key,
                "data": [{"WORK_DT": job_params["date"], dataset_key: 1}],
                "summary": dataset_key,
            }
        ]

    retrieval_planner.RETRIEVAL_RESULT_CACHE.clear()
    monkeypatch.setattr(retrieval_planner, "execute_retrieval_tools", fake_execute_retrieval_tools)

    jobs = [
        {"dataset_key": "production", "params": {"date": "20260410"}, "result_label": None},
        {"dataset_key": "target", "params": {"date": "20260410"}, "result_label": None},
        {"dataset_key": "wip", "params": {"date": "20260410"}, "result_label": None},
    ]
    results = retrieval_planner.execute_retrieval_jobs(jobs)

    assert [result["dataset_key"] for result in results] == ["production", "target", "wip"]
    assert len(thread_ids) >= 2


def test_sanitize_markdown_text_preserves_numeric_ranges_without_strikethrough():
    text = "목표 7,000~~7,200건 대비 약 20~~30% 잔여 생산"
    sanitized = sanitize_markdown_text(text)

    assert "7,000~7,200" in sanitized
    assert "20~30%" in sanitized
    assert "~~" not in sanitized


def test_generate_response_sanitizes_accidental_strikethrough(monkeypatch):
    monkeypatch.setattr(response_service, "get_llm_for_task", lambda *_args, **_kwargs: _FakeLLM("7,000~~7,200건 / 20~~30%"))

    result = response_service.generate_response(
        user_input="성과를 알려줘",
        result={"summary": "테스트", "data": [], "analysis_plan": {}},
        chat_history=[],
    )

    assert "7,000~7,200건" in result
    assert "20~30%" in result
    assert "~~" not in result


def test_plan_retrieval_request_uses_target_for_achievement_rate_synonym(monkeypatch):
    _stub_retrieval_planner_llm(
        monkeypatch,
        {
            "dataset_keys": ["production"],
            "needs_post_processing": True,
            "analysis_goal": "achievement by mode",
            "merge_hints": {
                "pre_aggregate_before_join": True,
                "group_dimensions": ["MODE"],
                "dataset_metrics": {"production": ["production"], "target": ["target"]},
                "aggregation": "sum",
                "reason": "grouped ratio question",
            },
        },
    )

    plan = retrieval_planner.plan_retrieval_request(
        "오늘 DA공정에서 DDR5제품의 생산 달성율을 알려줘",
        [],
        None,
    )

    assert set(plan["dataset_keys"]) == {"production", "target"}
    assert plan["merge_hints"]["pre_aggregate_before_join"] is True
    assert plan["merge_hints"]["group_dimensions"] == ["MODE"]


def test_normalize_dataset_result_columns_maps_external_production_column():
    result = {
        "success": True,
        "data": [
            {"WORK_DT": "20260408", "OPER_NAME": "D/A1", "PROD": 1234},
        ],
    }

    normalized = normalize_dataset_result_columns(result, "production")

    assert normalized["data"][0]["production"] == 1234
    assert normalized["column_rename_map"] == {"PROD": "production"}


def test_execute_retrieval_tools_normalizes_external_target_column(monkeypatch):
    def _fake_target_tool(_params):
        return {
            "success": True,
            "tool_name": "fake_target_tool",
            "data": [{"WORK_DT": "20260408", "OPER_NAME": "D/A1", "TARGET": 1400}],
            "summary": "fake target",
        }

    monkeypatch.setitem(retrieval_data.RETRIEVAL_TOOL_MAP, "target", _fake_target_tool)
    monkeypatch.setitem(
        retrieval_data.DATASET_REGISTRY,
        "target",
        {
            **retrieval_data.DATASET_REGISTRY["target"],
            "tool": _fake_target_tool,
        },
    )

    results = retrieval_data.execute_retrieval_tools(["target"], {"date": "20260408"})

    assert results[0]["data"][0]["target"] == 1400
    assert results[0]["column_rename_map"] == {"TARGET": "target"}


def test_build_analysis_base_table_preaggregates_before_ratio_join():
    tool_results = [
        {
            "success": True,
            "dataset_key": "production",
            "dataset_label": "생산",
            "tool_name": "get_production_data",
            "data": [
                {"WORK_DT": "20260408", "OPER_NAME": "W/B1", "MODE": "DDR5", "DEN": "256G", "TECH": "FC", "production": 100},
                {"WORK_DT": "20260408", "OPER_NAME": "W/B1", "MODE": "DDR5", "DEN": "512G", "TECH": "FC", "production": 120},
            ],
        },
        {
            "success": True,
            "dataset_key": "target",
            "dataset_label": "목표",
            "tool_name": "get_target_data",
            "data": [
                {"WORK_DT": "20260408", "OPER_NAME": "W/B1", "MODE": "DDR5", "DEN": "256G", "TECH": "FC", "target": 140},
                {"WORK_DT": "20260408", "OPER_NAME": "W/B1", "MODE": "DDR5", "DEN": "512G", "TECH": "FC", "target": 160},
            ],
        },
    ]

    analysis_base = build_analysis_base_table(
        tool_results,
        "임의 질문",
        retrieval_plan={
            "merge_hints": {
                "pre_aggregate_before_join": True,
                "group_dimensions": ["MODE"],
                "dataset_metrics": {"production": ["production"], "target": ["target"]},
                "aggregation": "sum",
                "reason": "group by MODE before join",
            }
        },
    )

    assert analysis_base["success"] is True
    assert analysis_base["join_columns"] == ["MODE"]
    assert analysis_base["data"] == [{"MODE": "DDR5", "production": 220, "target": 300}]
    assert any("LLM 힌트" in note for note in analysis_base["merge_notes"])


def test_build_analysis_base_table_uses_requested_dimension_when_llm_group_hint_is_missing():
    tool_results = [
        {
            "success": True,
            "dataset_key": "production",
            "dataset_label": "생산",
            "tool_name": "get_production_data",
            "data": [
                {"WORK_DT": "20260408", "OPER_NAME": "D/A1", "MODE": "DDR5", "production": 100},
                {"WORK_DT": "20260408", "OPER_NAME": "D/A2", "MODE": "DDR5", "production": 120},
            ],
        },
        {
            "success": True,
            "dataset_key": "target",
            "dataset_label": "목표",
            "tool_name": "get_target_data",
            "data": [
                {"WORK_DT": "20260408", "OPER_NAME": "D/A1", "MODE": "DDR5", "target": 130},
                {"WORK_DT": "20260408", "OPER_NAME": "D/A2", "MODE": "DDR5", "target": 150},
            ],
        },
    ]

    analysis_base = build_analysis_base_table(
        tool_results,
        "오늘 DA공정에서 DDR5제품의 생산 달성율을 공정별로 알려줘",
        retrieval_plan={
            "merge_hints": {
                "pre_aggregate_before_join": True,
                "group_dimensions": [],
                "dataset_metrics": {"production": ["production"], "target": ["target"]},
                "aggregation": "sum",
                "reason": "ratio question but group dimension missing",
            }
        },
    )

    assert analysis_base["success"] is True
    assert analysis_base["join_columns"] == ["OPER_NAME"]
    assert analysis_base["data"] == [
        {"OPER_NAME": "D/A1", "production": 100, "target": 130},
        {"OPER_NAME": "D/A2", "production": 120, "target": 150},
    ]
    assert any("보조 힌트" in note for note in analysis_base["merge_notes"])


def test_plan_retrieval_request_combines_achievement_and_saturation(monkeypatch):
    _stub_retrieval_planner_llm(
        monkeypatch,
        {
            "dataset_keys": ["production"],
            "needs_post_processing": False,
            "analysis_goal": "single dataset only",
        },
    )

    plan = retrieval_planner.plan_retrieval_request(
        "오늘 DA공정에서 DDR5제품의 생산 달성율과 생산 포화율을 알려줘",
        [],
        None,
    )

    assert set(plan["dataset_keys"]) == {"production", "target", "wip"}
    assert plan["needs_post_processing"] is True


def test_plan_retrieval_request_prefers_explicit_dataset_listing(monkeypatch):
    _stub_retrieval_planner_llm(
        monkeypatch,
        {
            "dataset_keys": ["production", "target", "defect"],
            "needs_post_processing": True,
            "analysis_goal": "wrong llm choice",
        },
    )

    plan = retrieval_planner.plan_retrieval_request(
        "오늘 생산량/재공/목표 값을 보여줘",
        [],
        None,
    )

    assert plan["dataset_keys"] == ["production", "target", "wip"]
    assert plan["needs_post_processing"] is False


def test_ensure_filtered_result_rows_applies_final_filter_to_display_table():
    raw_result = get_production_data({"date": "20260406"})
    raw_result["dataset_key"] = "production"
    raw_result["dataset_label"] = "생산"

    filtered_result = ensure_filtered_result_rows(
        raw_result,
        {"date": "20260406", "process_name": ["D/A1"], "mode": ["DDR5"]},
    )

    assert filtered_result["data"]
    assert all(row["OPER_NAME"] == "D/A1" for row in filtered_result["data"])
    assert all(row["MODE"] == "DDR5" for row in filtered_result["data"])


def test_build_analysis_base_table_handles_empty_dataset_without_index_error():
    params = {
        "date": "20260406",
        "process_name": ["D/A1"],
        "mode": ["DDR5"],
        "oper_num": None,
        "pkg_type1": None,
        "pkg_type2": None,
        "product_name": None,
        "line_name": None,
        "den": None,
        "tech": None,
        "lead": None,
        "mcp_no": None,
    }
    production = get_production_data(params)
    production["dataset_key"] = "production"
    production["dataset_label"] = "생산"

    target = retrieval_planner.execute_retrieval_jobs([{"dataset_key": "target", "params": params, "result_label": None}])[0]

    empty_wip = {
        "success": True,
        "tool_name": "get_wip_status",
        "dataset_key": "wip",
        "dataset_label": "WIP",
        "data": [],
        "summary": "총 0건",
    }

    result = build_analysis_base_table(
        [production, target, empty_wip],
        "오늘 DA공정에서 DDR5제품의 생산 달성율과 생산 포화율을 알려줘",
    )

    assert result["success"] is True
    assert result["data"]
