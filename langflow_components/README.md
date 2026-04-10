# Langflow Components Path

이 폴더는 `LANGFLOW_COMPONENTS_PATH` 에 바로 연결할 수 있는 실제 Langflow 컴포넌트 폴더입니다.

추천 설정값:

```powershell
$env:LANGFLOW_COMPONENTS_PATH="C:\Users\qkekt\Desktop\agent_langgraph_v2\langflow_components"
```

폴더 구조:

- `manufacturing_agent/`
  - Langflow가 읽는 카테고리 폴더
- `manufacturing_agent/manufacturing_agent_component.py`
  - Manufacturing Agent 단일 실행 컴포넌트
- `manufacturing_agent/manufacturing_state_input.py`
  - 입력 state 생성 컴포넌트
- `manufacturing_agent/resolve_manufacturing_request.py`
  - 질문 해석 컴포넌트
- `manufacturing_agent/plan_manufacturing_retrieval.py`
  - 조회 계획 컴포넌트
- `manufacturing_agent/run_manufacturing_branch.py`
  - 분기 실행 컴포넌트
- `manufacturing_agent/finish_manufacturing_result.py`
  - 결과 정리 컴포넌트
- `manufacturing_agent/__init__.py`
  - 컴포넌트 export 목록

실제 비즈니스 로직은 아래 공통 모듈을 그대로 사용합니다.

- `C:\Users\qkekt\Desktop\agent_langgraph_v2\langflow_version\components.py`
- `C:\Users\qkekt\Desktop\agent_langgraph_v2\langflow_version\workflow.py`
- `C:\Users\qkekt\Desktop\agent_langgraph_v2\manufacturing_agent`
