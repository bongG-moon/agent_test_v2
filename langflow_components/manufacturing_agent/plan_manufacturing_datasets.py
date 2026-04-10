"""Langflow custom component: Plan Manufacturing Datasets."""

from __future__ import annotations

import sys
from pathlib import Path

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output


def _ensure_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)


class PlanManufacturingDatasetsComponent(Component):
    display_name = "데이터셋 계획"
    description = "질문을 보고 어떤 제조 데이터셋이 필요한지 먼저 결정합니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "TableProperties"
    name = "plan_manufacturing_datasets"

    inputs = [DataInput(name="state", display_name="State", info="질의 모드가 판단된 state")]
    outputs = [Output(name="state_with_plan", display_name="계획 포함 State", method="plan_datasets")]

    def plan_datasets(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from manufacturing_agent.data.retrieval import pick_retrieval_tools
        from manufacturing_agent.services.retrieval_planner import plan_retrieval_request

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload

        retrieval_plan = plan_retrieval_request(
            state.get("user_input", ""),
            state.get("chat_history", []),
            state.get("current_data"),
        )
        retrieval_keys = retrieval_plan.get("dataset_keys") or pick_retrieval_tools(state.get("user_input", ""))
        updated_state = {
            **state,
            "retrieval_plan": retrieval_plan,
            "retrieval_keys": retrieval_keys,
        }
        self.status = f"데이터셋 계획 완료: {len(retrieval_keys)}개"
        return make_data({"state": updated_state})
