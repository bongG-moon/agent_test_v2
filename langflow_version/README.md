# Langflow Version

이 폴더는 `manufacturing_agent`의 공통 로직을 재사용하면서 Langflow에서 쓰기 쉬운 형태로 감싼 구현입니다.

구성:

- `workflow.py`: LangGraph 런타임 없이도 같은 순서를 따라 실행할 수 있는 순수 파이썬 워크플로우
- `component_base.py`: Langflow 설치 유무와 상관없이 import/test가 가능하도록 만든 호환 레이어
- `components.py`: Langflow 커스텀 컴포넌트 클래스 모음

추천 사용 방식:

1. 먼저 `Manufacturing Agent` 단일 컴포넌트로 전체 기능을 확인합니다.
2. 세밀하게 제어하고 싶으면 아래 순서로 컴포넌트를 연결합니다.
3. `Manufacturing State Input` -> `Resolve Manufacturing Request` -> `Run Manufacturing Branch` -> `Finish Manufacturing Result`

참고:

- 실제 Langflow에 올릴 때는 `LANGFLOW_COMPONENTS_PATH`에 이 폴더를 포함하거나, 카테고리 구조에 맞게 복사해 사용하면 됩니다.
- 이 구현은 기존 제조 도메인/데이터 로직을 유지하고, Langflow에서 요구하는 입력/출력 포맷만 얇게 감쌉니다.
