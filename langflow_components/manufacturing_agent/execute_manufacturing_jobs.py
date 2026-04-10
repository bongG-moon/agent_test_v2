"""Langflow custom component: Execute Manufacturing Jobs."""

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


class ExecuteManufacturingJobsComponent(Component):
    display_name = "조회 Job 실행"
    description = "생성된 제조 조회 job들을 실제로 실행하고 원본 결과를 state에 담습니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Play"
    name = "execute_manufacturing_jobs"

    inputs = [DataInput(name="state", display_name="State", info="retrieval_jobs가 포함된 state")]
    outputs = [Output(name="state_with_source_results", display_name="조회 결과 포함 State", method="execute_jobs")]

    def execute_jobs(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from manufacturing_agent.data.retrieval import build_current_datasets
        from manufacturing_agent.services.request_context import attach_result_metadata
        from manufacturing_agent.services.retrieval_planner import execute_retrieval_jobs
        from manufacturing_agent.services.runtime_service import ensure_filtered_result_rows

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        jobs = state.get("retrieval_jobs", [])
        if not jobs:
            self.status = "실행할 job이 없어 기존 state 유지"
            return make_data({"state": state})

        source_results = execute_retrieval_jobs(jobs)
        for result, job in zip(source_results, jobs):
            attach_result_metadata(result, job["params"], result.get("tool_name", ""))
        source_results = [
            ensure_filtered_result_rows(result, job["params"])
            for result, job in zip(source_results, jobs)
        ]

        updated_state = {
            **state,
            "source_results": source_results,
            "current_datasets": build_current_datasets(source_results),
        }
        self.status = f"조회 job 실행 완료: {len(source_results)}개 결과"
        return make_data({"state": updated_state})
