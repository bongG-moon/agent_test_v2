"""Langflow custom components for the manufacturing agent.

These classes reuse the shared manufacturing_agent service layer. They can be
loaded into Langflow as custom components, or imported locally for testing.
"""

from __future__ import annotations

from typing import Any, Dict

from .component_base import Component, DataInput, MessageTextInput, MultilineInput, Output, make_data, read_data_payload
from .workflow import (
    build_initial_state,
    finish_step,
    plan_retrieval_step,
    resolve_request_step,
    run_langflow_workflow,
    run_next_branch,
)


def _state_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    state = payload.get("state")
    return state if isinstance(state, dict) else payload


class ManufacturingStateComponent(Component):
    display_name = "Manufacturing State Input"
    description = "Build the shared state dictionary used by Langflow manufacturing components."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Package"
    name = "manufacturing_state_input"

    inputs = [
        MessageTextInput(name="user_input", display_name="User Input", info="Natural-language manufacturing question."),
        MultilineInput(name="chat_history", display_name="Chat History JSON", info="Optional JSON list of chat messages."),
        MultilineInput(name="context", display_name="Context JSON", info="Optional JSON dictionary of inherited filters."),
        MultilineInput(name="current_data", display_name="Current Data JSON", info="Optional current table/result payload."),
    ]
    outputs = [Output(name="state", display_name="State", method="build_state")]

    def build_state(self):
        state = build_initial_state(
            user_input=getattr(self, "user_input", ""),
            chat_history=getattr(self, "chat_history", None),
            context=getattr(self, "context", None),
            current_data=getattr(self, "current_data", None),
        )
        self.status = "Initial state created"
        return make_data({"state": state})


class ResolveRequestComponent(Component):
    display_name = "Resolve Manufacturing Request"
    description = "Extract filters and choose whether to retrieve new data or analyze the current table."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Route"
    name = "resolve_manufacturing_request"

    inputs = [DataInput(name="state", display_name="State", info="State created by Manufacturing State Input.")]
    outputs = [Output(name="state", display_name="Resolved State", method="resolve_state")]

    def resolve_state(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = resolve_request_step(_state_from_payload(payload))
        self.status = f"Request resolved with mode={state.get('query_mode', 'unknown')}"
        return make_data({"state": state})


class PlanRetrievalComponent(Component):
    display_name = "Plan Manufacturing Retrieval"
    description = "Choose raw datasets and build retrieval jobs for the manufacturing question."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Database"
    name = "plan_manufacturing_retrieval"

    inputs = [DataInput(name="state", display_name="State", info="Resolved state from the previous component.")]
    outputs = [Output(name="state", display_name="Planned State", method="plan_state")]

    def plan_state(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = plan_retrieval_step(_state_from_payload(payload))
        planned_jobs = len(state.get("retrieval_jobs", []))
        self.status = f"Retrieval planned with {planned_jobs} job(s)"
        return make_data({"state": state})


class RunWorkflowBranchComponent(Component):
    display_name = "Run Manufacturing Branch"
    description = "Execute the next workflow branch based on the current state."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitBranch"
    name = "run_manufacturing_branch"

    inputs = [DataInput(name="state", display_name="State", info="State after request resolution.")]
    outputs = [Output(name="state", display_name="Updated State", method="run_branch")]

    def run_branch(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = run_next_branch(_state_from_payload(payload))
        has_result = bool(state.get("result"))
        self.status = "Branch executed" if has_result else "Branch executed without final result"
        return make_data({"state": state})


class FinishManufacturingResultComponent(Component):
    display_name = "Finish Manufacturing Result"
    description = "Normalize the final state and expose the result payload."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "CheckCheck"
    name = "finish_manufacturing_result"

    inputs = [DataInput(name="state", display_name="State", info="State returned by Run Manufacturing Branch.")]
    outputs = [
        Output(name="state", display_name="Finished State", method="finish_state", group_outputs=True),
        Output(name="result", display_name="Result", method="result_data", group_outputs=True),
    ]

    def finish_state(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = finish_step(_state_from_payload(payload))
        self.status = "Result normalized"
        return make_data({"state": state})

    def result_data(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = finish_step(_state_from_payload(payload))
        return make_data(state.get("result", {}))


class ManufacturingAgentComponent(Component):
    display_name = "Manufacturing Agent"
    description = "Run the full manufacturing workflow in one Langflow component."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Bot"
    name = "manufacturing_agent_component"

    inputs = [
        MessageTextInput(name="user_input", display_name="User Input", info="Natural-language manufacturing question."),
        MultilineInput(name="chat_history", display_name="Chat History JSON", info="Optional JSON list of chat messages."),
        MultilineInput(name="context", display_name="Context JSON", info="Optional JSON dictionary of inherited filters."),
        MultilineInput(name="current_data", display_name="Current Data JSON", info="Optional current result/table payload."),
    ]
    outputs = [Output(name="result", display_name="Result", method="run_component")]

    def run_component(self):
        result = run_langflow_workflow(
            user_input=getattr(self, "user_input", ""),
            chat_history=getattr(self, "chat_history", None),
            context=getattr(self, "context", None),
            current_data=getattr(self, "current_data", None),
        )
        self.status = f"Workflow complete with success={bool(result.get('tool_results'))}"
        return make_data(result)
