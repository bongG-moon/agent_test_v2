from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output
from langflow.schema import Data


class MinimalCustomComponent(Component):
    display_name = "Minimal Custom Component"
    description = "가장 단순한 형태의 Langflow 커스텀 노드 예시입니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Bot"
    name = "minimal_custom_component"

    inputs = [
        MessageTextInput(
            name="user_text",
            display_name="입력 텍스트",
            info="아무 문자열이나 넣어보세요.",
        )
    ]

    outputs = [
        Output(
            name="result_data",
            display_name="결과",
            method="build_result",
        )
    ]

    def build_result(self) -> Data:
        text = getattr(self, "user_text", "")
        result = {
            "original_text": text,
            "message": f"입력된 텍스트는 '{text}' 입니다.",
        }
        self.status = "최소 예제 실행 완료"
        return Data(data=result)
