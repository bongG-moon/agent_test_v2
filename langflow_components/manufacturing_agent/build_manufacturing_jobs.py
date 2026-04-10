"""Langflow custom component: Build Manufacturing Jobs."""

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


class BuildManufacturingJobsComponent(Component):
    display_name = "조회 Job 생성"
    description = "선택된 데이터셋과 추출된 파라미터로 실제 조회 job 목록을 만듭니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "ListChecks"
    name = "build_manufacturing_jobs"

    inputs = [DataInput(name="state", display_name="State", info="데이터셋 계획이 포함된 state")]
    outputs = [Output(name="state_with_jobs", display_name="Job 포함 State", method="build_jobs")]

    def build_jobs(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from manufacturing_agent.data.retrieval import dataset_requires_date
        from manufacturing_agent.services.request_context import build_unknown_retrieval_message, has_current_data
        from manufacturing_agent.services.retrieval_planner import build_missing_date_message, build_retrieval_jobs

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        retrieval_keys = state.get("retrieval_keys", [])
        extracted_params = state.get("extracted_params", {})
        current_data = state.get("current_data")
        user_input = state.get("user_input", "")

        if not retrieval_keys:
            updated_state = {
                **state,
                "retrieval_jobs": [],
                "result": {
                    "response": build_unknown_retrieval_message(),
                    "tool_results": [],
                    "current_data": current_data,
                    "extracted_params": extracted_params,
                    "awaiting_analysis_choice": bool(has_current_data(current_data)),
                },
            }
            self.status = "조회할 데이터셋이 없어 job 생성 중단"
            return make_data({"state": updated_state})

        jobs = build_retrieval_jobs(user_input, extracted_params, retrieval_keys)
        missing_date_jobs = [job for job in jobs if dataset_requires_date(job["dataset_key"]) and not job["params"].get("date")]

        if missing_date_jobs:
            updated_state = {
                **state,
                "retrieval_jobs": jobs,
                "result": {
                    "response": build_missing_date_message([job["dataset_key"] for job in missing_date_jobs]),
                    "tool_results": [],
                    "current_data": current_data,
                    "extracted_params": extracted_params,
                    "awaiting_analysis_choice": bool(has_current_data(current_data)),
                },
            }
            self.status = "날짜 조건이 없어 일부 job 생성 보류"
            return make_data({"state": updated_state})

        updated_state = {**state, "retrieval_jobs": jobs}
        self.status = f"조회 job 생성 완료: {len(jobs)}개"
        return make_data({"state": updated_state})
