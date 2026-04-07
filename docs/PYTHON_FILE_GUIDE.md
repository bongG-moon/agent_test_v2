# Python File Guide

이 문서는 주요 Python 파일이 왜 존재하는지 빠르게 파악하기 위한 안내서입니다.

## 먼저 기억할 점

- 실제 코어 로직은 [manufacturing_agent](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent)에 있습니다.
- Langflow 전용 구현은 [langflow_version](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version)에 따로 있습니다.
- 외부 연동용 얇은 래퍼 함수는 지금 [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)에 함께 들어 있습니다.
- 그래프 분기 함수는 지금 [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)에 함께 들어 있습니다.

## 추천 읽기 순서

1. [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)
2. [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
3. [manufacturing_agent/graph/state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)
4. [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
5. [manufacturing_agent/graph/nodes](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes)
6. [manufacturing_agent/services](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services)
7. [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)
8. [manufacturing_agent/domain/knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)
9. [manufacturing_agent/domain/registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/registry.py)
10. [manufacturing_agent/analysis](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis)
11. [langflow_version](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version)

## Root Files

### [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)
- Streamlit 앱의 실제 시작 파일입니다.
- 사용자 입력을 받고, `run_agent()`를 호출하고, 결과를 화면에 그립니다.

### [ui_renderer.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/ui_renderer.py)
- 루트 경로 호환용 파일입니다.
- 실제 구현은 [manufacturing_agent/app/ui_renderer.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app/ui_renderer.py)에 있습니다.

### [ui_domain_knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/ui_domain_knowledge.py)
- 루트 경로 호환용 파일입니다.
- 실제 구현은 [manufacturing_agent/app/ui_domain_knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app/ui_domain_knowledge.py)에 있습니다.

## manufacturing_agent

### [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
- 에이전트의 대표 진입점입니다.
- `run_agent()`는 LangGraph 전체 흐름을 실행합니다.
- `extract_params_component()` 같은 함수들은 Langflow나 외부 노드 시스템에서 재사용할 수 있는 얇은 래퍼입니다.

### [manufacturing_agent/graph/state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)
- 모든 노드가 공유하는 상태 구조를 정의합니다.

### [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
- LangGraph를 조립합니다.
- 그래프 노드 등록, 분기 함수, 시작점과 종료점이 모두 이 파일에 있습니다.

### [manufacturing_agent/graph/nodes/resolve_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/resolve_request.py)
- 질문 해석 시작 노드입니다.

### [manufacturing_agent/graph/nodes/plan_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/plan_retrieval.py)
- 어떤 dataset이 필요한지 계획합니다.

### [manufacturing_agent/graph/nodes/retrieve_single.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_single.py)
- 단일 dataset 조회 경로를 담당합니다.

### [manufacturing_agent/graph/nodes/retrieve_multi.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_multi.py)
- 다중 dataset 또는 다중 날짜 조회 경로를 담당합니다.

### [manufacturing_agent/graph/nodes/followup_analysis.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/followup_analysis.py)
- 현재 화면의 결과를 다시 가공하는 후속 분석을 담당합니다.

### [manufacturing_agent/graph/nodes/finish.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/finish.py)
- 마지막 결과를 정리합니다.

## services

### [manufacturing_agent/services/request_context.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/request_context.py)
- 현재 질문의 문맥을 정리합니다.

### [manufacturing_agent/services/parameter_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/parameter_service.py)
- 질문에서 날짜, 공정, MODE, 제품, 라인 같은 조회 조건을 추출합니다.

### [manufacturing_agent/services/query_mode.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/query_mode.py)
- 새 데이터를 조회해야 하는 질문인지, 현재 결과를 재가공하는 질문인지 판단합니다.

### [manufacturing_agent/services/retrieval_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/retrieval_planner.py)
- 어떤 dataset 조합이 필요한지 계획하고 조회 job 목록을 만듭니다.

### [manufacturing_agent/services/merge_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/merge_service.py)
- 여러 dataset을 분석 가능한 하나의 표로 합칩니다.

### [manufacturing_agent/services/runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)
- retrieval과 후처리 분석 실행을 조율합니다.

### [manufacturing_agent/services/response_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/response_service.py)
- 최종 자연어 응답을 생성합니다.

## analysis

### [manufacturing_agent/analysis/contracts.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/contracts.py)
- 분석 단계 자료구조를 정의합니다.

### [manufacturing_agent/analysis/helpers.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/helpers.py)
- 컬럼 탐색과 fallback 보조 함수를 모아둡니다.

### [manufacturing_agent/analysis/llm_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/llm_planner.py)
- LLM 분석 계획 프롬프트를 만듭니다.

### [manufacturing_agent/analysis/safe_executor.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/safe_executor.py)
- 생성된 pandas 코드를 안전하게 검사하고 실행합니다.

### [manufacturing_agent/analysis/engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/engine.py)
- 분석 엔진의 중심 파일입니다.

## data

### [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)
- mock 제조 데이터 생성과 조회를 담당합니다.

## domain

### [manufacturing_agent/domain/knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)
- 제조 도메인의 기본 상수와 규칙을 담습니다.

### [manufacturing_agent/domain/registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/registry.py)
- 사용자 정의 도메인 규칙을 저장하고 조회합니다.

## app

### [manufacturing_agent/app/ui_renderer.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app/ui_renderer.py)
- Streamlit 채팅 화면과 결과 표 렌더링을 담당합니다.

### [manufacturing_agent/app/ui_domain_knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app/ui_domain_knowledge.py)
- 사용자 정의 도메인 규칙 UI를 담당합니다.

## shared

### [manufacturing_agent/shared/config.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/shared/config.py)
- 공통 LLM 설정을 관리합니다.

### [manufacturing_agent/shared/filter_utils.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/shared/filter_utils.py)
- 공통 문자열/필터 유틸을 제공합니다.

### [manufacturing_agent/shared/number_format.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/shared/number_format.py)
- 숫자 포맷팅을 담당합니다.

### [manufacturing_agent/shared/text_sanitizer.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/shared/text_sanitizer.py)
- 마크다운 취소선 문제 같은 렌더링 이슈를 막기 위한 텍스트 정리를 담당합니다.

## langflow_version

### [langflow_version/component_base.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/component_base.py)
- Langflow 미설치 환경용 호환 레이어입니다.

### [langflow_version/workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)
- LangGraph 없이도 같은 순서로 단계를 실행하는 워크플로우입니다.

### [langflow_version/components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)
- Langflow 커스텀 컴포넌트를 정의합니다.

## scripts 와 tests

### [scripts/run_validation_scenarios.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/scripts/run_validation_scenarios.py)
- 질문 시나리오를 한 번에 검증하는 스크립트입니다.

### [tests/conftest.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/tests/conftest.py)
- 테스트 실행용 기본 설정 파일입니다.

### [tests/test_v2_structure.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/tests/test_v2_structure.py)
- 기본 구조, 파라미터 추출, Langflow 경로, 텍스트 sanitize까지 검증합니다.
