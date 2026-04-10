# Langflow Components Path

이 폴더는 `LANGFLOW_COMPONENTS_PATH` 에 바로 연결할 수 있는 실제 Langflow 컴포넌트 폴더입니다.

추천 설정값:

```powershell
$env:LANGFLOW_COMPONENTS_PATH="C:\Users\qkekt\Desktop\agent_langgraph_v2\langflow_components"
```

폴더 구조:

- `manufacturing_agent/`
  - Langflow가 읽는 카테고리 폴더
- `manufacturing_agent/manufacturing_components.py`
  - 실제 커스텀 컴포넌트 진입점
- `manufacturing_agent/__init__.py`
  - 컴포넌트 export 목록

실제 비즈니스 로직은 아래 공통 모듈을 그대로 사용합니다.

- `C:\Users\qkekt\Desktop\agent_langgraph_v2\langflow_version\components.py`
- `C:\Users\qkekt\Desktop\agent_langgraph_v2\langflow_version\workflow.py`
- `C:\Users\qkekt\Desktop\agent_langgraph_v2\manufacturing_agent`
