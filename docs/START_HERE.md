# Start Here

이 프로젝트를 처음 읽는다면 가장 먼저 봐야 할 경로는 `manufacturing_agent/` 입니다.

핵심만 먼저 보면:

1. [agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
2. [state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)
3. [builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
4. [resolve_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/resolve_request.py)
5. [plan_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/plan_retrieval.py)
6. [runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)
7. [retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)
8. [knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)

한 줄 흐름으로 보면 이렇게 이해하면 됩니다.

`질문 입력 -> 파라미터 추출 -> 새 데이터 조회 여부 판단 -> 필요한 dataset 계획 -> 조회 실행 -> 필요 시 병합/분석 -> 응답 생성`

## 폴더를 한 번에 이해하는 방법

- `manufacturing_agent/graph/`
  - 실행 순서를 담당합니다.
- `manufacturing_agent/services/`
  - 실제 비즈니스 로직을 담당합니다.
- `manufacturing_agent/data/`
  - 제조 mock dataset 을 만듭니다.
- `manufacturing_agent/domain/`
  - 제조 도메인 지식과 사용자 등록 규칙을 가집니다.
- `manufacturing_agent/analysis/`
  - pandas 기반 후처리 분석을 담당합니다.
- `langflow_version/`
  - 같은 코어 로직을 Langflow 스타일로 감싼 전용 레이어입니다.

## 처음 읽을 때 팁

- 먼저 `graph` 와 `services` 의 연결을 이해하면 전체가 훨씬 쉬워집니다.
- “노드는 얇고, 서비스가 실제 일을 한다”는 기준으로 읽으면 구조가 잘 보입니다.

## 같이 보면 좋은 문서

- [README.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/README.md)
- [PYTHON_FILE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/PYTHON_FILE_GUIDE.md)
- [FUNCTION_ROLE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/FUNCTION_ROLE_GUIDE.md)
- [LANGFLOW_VERSION.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_VERSION.md)
- [BEGINNER_LEARNING_PATH.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/BEGINNER_LEARNING_PATH.md)
