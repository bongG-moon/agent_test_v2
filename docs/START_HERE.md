# Start Here

이 프로젝트를 처음 읽는다면 가장 먼저 봐야 할 경로는 [manufacturing_agent](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent) 입니다.

## 가장 먼저 읽을 파일

1. [agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
2. [state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)
3. [builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
4. [resolve_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/resolve_request.py)
5. [plan_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/plan_retrieval.py)
6. [runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)
7. [retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)
8. [knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)

## 한 줄 흐름

`질문 입력 -> 파라미터 추출 -> follow-up 여부 판단 -> 필요한 dataset 계획 -> 조회 실행 -> 병합/분석 -> 응답 생성`

## 폴더를 보는 기준

- `manufacturing_agent/graph/`
  - 실행 순서와 분기를 담습니다.
- `manufacturing_agent/services/`
  - 실제 핵심 로직이 있습니다.
- `manufacturing_agent/data/`
  - 제조 mock 데이터를 조회합니다.
- `manufacturing_agent/domain/`
  - 공정, 제품, 사용자 정의 규칙 같은 도메인 지식을 가집니다.
- `manufacturing_agent/analysis/`
  - pandas 기반 후처리 분석을 담당합니다.
- `langflow_version/`
  - 같은 코어 로직을 Langflow 컴포넌트로 감싸는 레이어입니다.

## 지금 구조에서 기억하면 좋은 점

- `manufacturing_agent/agent.py`는 단순 진입점이 아닙니다.
  - `run_agent()`로 LangGraph 실행을 시작합니다.
  - Langflow나 다른 외부 시스템이 바로 쓸 수 있는 `dict -> dict` 래퍼 함수도 함께 제공합니다.
- `manufacturing_agent/graph/builder.py`는 그래프 조립만 하지 않습니다.
  - 라우팅 함수도 같이 가지고 있어서, 그래프의 분기 규칙을 한 파일에서 읽을 수 있습니다.
- `services/`가 실제 핵심입니다.
  - 질문 해석, 조회 계획, 병합, 응답 생성이 여기 있습니다.

## 같이 보면 좋은 문서

- [README.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/README.md)
- [ARCHITECTURE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/ARCHITECTURE.md)
- [PYTHON_FILE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/PYTHON_FILE_GUIDE.md)
- [FUNCTION_ROLE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/FUNCTION_ROLE_GUIDE.md)
