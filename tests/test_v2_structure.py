from pathlib import Path

from langflow_version.components import ManufacturingAgentComponent
from langflow_version.workflow import build_initial_state, resolve_request_step, run_langflow_workflow
from manufacturing_agent.agent import extract_params_component, run_agent
from manufacturing_agent.domain import registry
from manufacturing_agent.services import parameter_service, request_context, response_service
from manufacturing_agent.services.query_mode import choose_query_mode
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


def test_sanitize_markdown_text_preserves_numeric_ranges_without_strikethrough():
    text = "목표 7,000~~7,200건 대비 약 20~~30% 잔여 생산량"
    sanitized = sanitize_markdown_text(text)

    assert "7,000~7,200" in sanitized
    assert "20~30%" in sanitized
    assert "~~" not in sanitized


def test_generate_response_sanitizes_accidental_strikethrough(monkeypatch):
    monkeypatch.setattr(response_service, "get_llm_for_task", lambda *_args, **_kwargs: _FakeLLM("7,000~~7,200건 / 20~~30%"))

    result = response_service.generate_response(
        user_input="달성률 알려줘",
        result={"summary": "테스트", "data": [], "analysis_plan": {}},
        chat_history=[],
    )

    assert "7,000~7,200건" in result
    assert "20~30%" in result
    assert "~~" not in result
