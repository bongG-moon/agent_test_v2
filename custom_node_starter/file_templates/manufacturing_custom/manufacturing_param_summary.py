"""파일 기반 커스텀 노드 예시: 제조 파라미터 요약."""

from __future__ import annotations

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output
from lfx.schema import Data


class ManufacturingParamSummaryComponent(Component):
    display_name = "Manufacturing Param Summary"
    description = "state 안의 extracted_params를 간단히 요약해서 보여주는 파일 기반 예시 노드입니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Filter"
    name = "manufacturing_param_summary"

    inputs = [
        DataInput(
            name="state",
            display_name="State",
            info="이전 노드에서 전달된 state",
        )
    ]

    outputs = [
        Output(
            name="summary_data",
            display_name="요약 결과",
            method="summarize_params",
        )
    ]

    def summarize_params(self) -> Data:
        incoming = getattr(self, "state", None)
        payload = getattr(incoming, "data", incoming) if incoming is not None else {}
        state = payload.get("state") if isinstance(payload, dict) and isinstance(payload.get("state"), dict) else payload
        extracted_params = state.get("extracted_params", {}) if isinstance(state, dict) else {}

        result = {
            "date": extracted_params.get("date"),
            "process_name": extracted_params.get("process_name"),
            "product_name": extracted_params.get("product_name"),
            "mode": extracted_params.get("mode"),
            "group_by": extracted_params.get("group_by"),
        }
        self.status = "파일 기반 커스텀 노드 실행 완료"
        return Data(data=result)
