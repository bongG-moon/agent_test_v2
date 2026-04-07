# Beginner Learning Path

이 문서는 Python 초보자가 이 프로젝트를 어떤 순서로 읽으면 좋은지 단계별로 안내합니다.

목표:

- 하루 안에 전체 흐름 이해하기
- 주요 파일이 어디에 있는지 익히기
- 나중에 작은 수정도 할 수 있게 만들기

## 1단계: 전체 그림 익히기

먼저 아래 문서만 읽습니다.

1. [README.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/README.md)
2. [docs/START_HERE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/START_HERE.md)
3. [docs/ARCHITECTURE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/ARCHITECTURE.md)

## 2단계: 실제 실행 입구 보기

다음 파일을 읽습니다.

1. [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)
2. [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
3. [manufacturing_agent/graph/state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)

## 3단계: 그래프 흐름 보기

다음 파일을 읽습니다.

1. [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
2. [manufacturing_agent/graph/nodes/resolve_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/resolve_request.py)
3. [manufacturing_agent/graph/nodes/plan_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/plan_retrieval.py)
4. [manufacturing_agent/graph/nodes/retrieve_single.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_single.py)
5. [manufacturing_agent/graph/nodes/retrieve_multi.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_multi.py)
6. [manufacturing_agent/graph/nodes/followup_analysis.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/followup_analysis.py)

핵심 포인트:

- 분기 함수는 이제 `builder.py` 안에 있습니다.
- 노드는 얇게, 실제 로직은 서비스 계층에 있습니다.

## 4단계: 서비스 계층 이해하기

다음 파일을 읽습니다.

1. [manufacturing_agent/services/parameter_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/parameter_service.py)
2. [manufacturing_agent/services/query_mode.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/query_mode.py)
3. [manufacturing_agent/services/retrieval_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/retrieval_planner.py)
4. [manufacturing_agent/services/runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)
5. [manufacturing_agent/services/merge_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/merge_service.py)
6. [manufacturing_agent/services/response_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/response_service.py)

## 5단계: 도메인과 데이터 이해하기

다음 파일을 읽습니다.

1. [manufacturing_agent/domain/knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)
2. [manufacturing_agent/domain/registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/registry.py)
3. [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)

## 6단계: 분석 엔진 보기

다음 파일을 읽습니다.

1. [manufacturing_agent/analysis/contracts.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/contracts.py)
2. [manufacturing_agent/analysis/helpers.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/helpers.py)
3. [manufacturing_agent/analysis/llm_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/llm_planner.py)
4. [manufacturing_agent/analysis/safe_executor.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/safe_executor.py)
5. [manufacturing_agent/analysis/engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/engine.py)

## 7단계: Langflow 버전 보기

다음 파일을 읽습니다.

1. [docs/LANGFLOW_VERSION.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_VERSION.md)
2. [docs/LANGFLOW_CANVAS_EXAMPLE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_CANVAS_EXAMPLE.md)
3. [langflow_version/workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)
4. [langflow_version/components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)

## 처음 수정해보기 좋은 주제

1. [response_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/response_service.py)의 응답 문구 조정
2. [knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)의 설명 보강
3. [query_mode.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/query_mode.py)의 규칙 추가
4. [retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)의 mock summary 문구 조정

## 처음부터 크게 건드리지 않는 것이 좋은 곳

1. [engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/engine.py)의 전체 흐름
2. [merge_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/merge_service.py)의 cardinality 로직
3. LangGraph와 Langflow 경로를 동시에 크게 바꾸는 작업
