"""Langflow custom component: Plan Manufacturing Retrieval."""

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


class PlanRetrievalComponent(Component):
    display_name = "조회 계획"
    description = "질문에 필요한 원천 데이터셋과 조회 job을 만듭니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Database"
    name = "plan_manufacturing_retrieval"

    inputs = [DataInput(name="state", display_name="State", info="질문 해석 단계가 끝난 state")]
    outputs = [Output(name="planned_state", display_name="계획된 State", method="plan_state")]

    def plan_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from langflow_version.workflow import plan_retrieval_step

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        planned = plan_retrieval_step(state)
        planned_jobs = len(planned.get("retrieval_jobs", []))
        self.status = f"조회 계획 완료: {planned_jobs}개 job"
        return make_data({"state": planned})
