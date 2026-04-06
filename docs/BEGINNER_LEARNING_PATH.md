# Beginner Learning Path

이 문서는 Python 초보자가 이 프로젝트를 어떤 순서로 읽으면 좋은지 단계별로 안내합니다.

목표:

- 하루 안에 전체 흐름을 이해하기
- 일주일 안에 작은 수정이 가능해지기
- 이후 Langflow 커스텀 노드까지 이어서 볼 수 있게 하기

## 1단계: 전체 그림 익히기

먼저 이 파일들만 읽습니다.

1. [README.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/README.md)
2. [docs/START_HERE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/START_HERE.md)
3. [docs/ARCHITECTURE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/ARCHITECTURE.md)

이 단계의 목표:

- 프로젝트가 무엇을 하는지 이해
- `graph`, `services`, `data`, `domain` 이 어떤 역할인지 이해

## 2단계: 실제 실행 입구 보기

다음 파일을 읽습니다.

1. [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)
2. [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
3. [manufacturing_agent/graph/state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)

이 단계에서 볼 포인트:

- 사용자의 질문이 어디로 들어가는지
- 어떤 상태 딕셔너리가 만들어지는지
- 최종 결과가 어떤 형태로 나오는지

## 3단계: 그래프 흐름 보기

다음 파일을 읽습니다.

1. [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
2. [manufacturing_agent/graph/routes.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/routes.py)
3. [manufacturing_agent/graph/nodes/resolve_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/resolve_request.py)
4. [manufacturing_agent/graph/nodes/plan_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/plan_retrieval.py)
5. [manufacturing_agent/graph/nodes/retrieve_single.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_single.py)
6. [manufacturing_agent/graph/nodes/retrieve_multi.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_multi.py)
7. [manufacturing_agent/graph/nodes/followup_analysis.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/followup_analysis.py)

이 단계의 목표:

- “노드는 얇다”는 감각 익히기
- 분기가 어디서 갈리는지 이해
- 실제 계산은 `services/` 가 한다는 점 이해

## 4단계: 서비스 계층 익히기

다음 파일을 읽습니다.

1. [manufacturing_agent/services/parameter_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/parameter_service.py)
2. [manufacturing_agent/services/query_mode.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/query_mode.py)
3. [manufacturing_agent/services/retrieval_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/retrieval_planner.py)
4. [manufacturing_agent/services/runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)
5. [manufacturing_agent/services/merge_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/merge_service.py)
6. [manufacturing_agent/services/response_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/response_service.py)

이 단계의 목표:

- 프로젝트의 핵심 로직이 어디 있는지 이해
- 질문 해석, 조회 계획, 실행, 응답 생성이 어떻게 나뉘는지 이해

## 5단계: 도메인과 데이터 이해하기

다음 파일을 읽습니다.

1. [manufacturing_agent/domain/knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)
2. [manufacturing_agent/domain/registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/registry.py)
3. [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)

이 단계의 목표:

- DA, WB 같은 공정군이 어디서 관리되는지 이해
- mock 데이터가 어떻게 생성되는지 이해
- custom domain rule 이 어디에 반영되는지 이해

## 6단계: 분석 엔진 이해하기

다음 파일을 읽습니다.

1. [manufacturing_agent/analysis/contracts.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/contracts.py)
2. [manufacturing_agent/analysis/helpers.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/helpers.py)
3. [manufacturing_agent/analysis/llm_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/llm_planner.py)
4. [manufacturing_agent/analysis/safe_executor.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/safe_executor.py)
5. [manufacturing_agent/analysis/engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/engine.py)

이 단계의 목표:

- 왜 후처리 분석이 별도 계층인지 이해
- safe executor 가 왜 필요한지 이해
- fallback 분석이 어떻게 동작하는지 이해

## 7단계: Langflow 버전 보기

다음 파일을 읽습니다.

1. [docs/LANGFLOW_VERSION.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_VERSION.md)
2. [docs/LANGFLOW_CANVAS_EXAMPLE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_CANVAS_EXAMPLE.md)
3. [langflow_version/workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)
4. [langflow_version/components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)

이 단계의 목표:

- LangGraph와 Langflow가 같은 코어를 공유한다는 점 이해
- custom component 를 어디서 어떻게 붙일지 감 잡기

## 처음 수정해보기 좋은 주제

초보자에게 추천하는 첫 수정:

1. `response_service.py` 의 응답 문구 조금 바꾸기
2. `domain/knowledge.py` 에 dataset 설명 한 줄 추가하기
3. `query_mode.py` 에 새 키워드 하나 추가하기
4. `data/retrieval.py` 의 mock summary 문구 조정하기

조금 익숙해지면 해볼 수정:

1. 새 dataset keyword 추가
2. 새 custom analysis rule 등록 흐름 확인
3. Langflow 컴포넌트 출력 포맷 확장

## 피하는 것이 좋은 첫 수정

처음부터 아래를 건드리면 어렵습니다.

1. `analysis/engine.py` 의 실행 흐름 전체 변경
2. `merge_service.py` 의 cardinality 로직 변경
3. LangGraph와 Langflow 레이어를 동시에 크게 바꾸기

## 추천 공부 순서 요약

하루 차:

1. `README`
2. `START_HERE`
3. `app.py`
4. `agent.py`
5. `graph/`

이틀 차:

1. `services/`
2. `data/`
3. `domain/`

삼일 차 이후:

1. `analysis/`
2. `langflow_version/`
3. 테스트와 실제 수정

## 같이 보면 좋은 문서

- [docs/README.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/README.md)
- [docs/PYTHON_FILE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/PYTHON_FILE_GUIDE.md)
- [docs/FUNCTION_ROLE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/FUNCTION_ROLE_GUIDE.md)
