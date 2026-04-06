# Python File Guide

이 문서는 이 저장소 안의 `py` 파일이 각각 왜 존재하는지 빠르게 파악하기 위한 안내서입니다.

가장 중요한 원칙:

- 실제 v2 실행 경로는 `manufacturing_agent/` 입니다.
- `core/` 는 과거 구조를 유지하거나 참고하기 위한 레거시/호환 계층입니다.
- Langflow 전용 구현은 `langflow_version/` 에 따로 분리되어 있습니다.

## 추천 읽기 순서

1. `app.py`
2. `manufacturing_agent/agent.py`
3. `manufacturing_agent/graph/state.py`
4. `manufacturing_agent/graph/builder.py`
5. `manufacturing_agent/graph/nodes/*`
6. `manufacturing_agent/services/*`
7. `manufacturing_agent/data/retrieval.py`
8. `manufacturing_agent/domain/knowledge.py`
9. `manufacturing_agent/domain/registry.py`
10. `manufacturing_agent/analysis/*`
11. `langflow_version/*`

## Root Files

### [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)
- Streamlit 앱의 실제 시작 파일입니다.
- 채팅 입력, 세션 상태, 도메인 페이지, 결과 렌더링을 연결합니다.
- 내부의 `_run_chat_turn()` 이 `manufacturing_agent.agent.run_agent()` 를 호출합니다.

### [ui_renderer.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/ui_renderer.py)
- 루트 경로 호환용 래퍼입니다.
- 실제 구현은 `manufacturing_agent.app.ui_renderer` 를 다시 export 합니다.

### [ui_domain_knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/ui_domain_knowledge.py)
- 루트 경로 호환용 래퍼입니다.
- 실제 구현은 `manufacturing_agent.app.ui_domain_knowledge` 에 있습니다.

## `manufacturing_agent/` 실제 v2 구현

### [manufacturing_agent/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
- 외부에서 가장 먼저 호출하는 엔트리 포인트입니다.
- 사용자 입력을 `AgentGraphState` 로 묶고 LangGraph를 실행한 뒤 최종 `result` 만 반환합니다.

## `manufacturing_agent/graph/`

### [manufacturing_agent/graph/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/graph/state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)
- 모든 노드가 공유하는 상태 구조를 정의합니다.
- 초보자가 “어떤 값이 어디서 생기고 다음 단계로 넘어가는지” 보기 위한 기준 파일입니다.

### [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
- LangGraph를 조립하는 파일입니다.
- 노드 등록, 조건 분기, 시작점과 종료점을 한 곳에서 보여줍니다.

### [manufacturing_agent/graph/routes.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/routes.py)
- 분기 판단만 담당합니다.
- 현재 데이터 재분석인지, 새 리트리벌인지, 단일/다중 리트리벌인지 결정합니다.

### [manufacturing_agent/graph/nodes/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/graph/nodes/resolve_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/resolve_request.py)
- 첫 번째 노드입니다.
- 질문에서 파라미터를 추출하고, 이후 흐름이 retrieval 인지 follow-up analysis 인지 결정합니다.

### [manufacturing_agent/graph/nodes/plan_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/plan_retrieval.py)
- 어떤 raw dataset 이 필요한지 계획합니다.
- 날짜가 없는 경우 바로 사용자 안내 메시지를 만들 수도 있습니다.

### [manufacturing_agent/graph/nodes/retrieve_single.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_single.py)
- 단일 dataset 조회 경로를 담당합니다.
- 필요하면 조회 직후 바로 후처리 분석도 붙입니다.

### [manufacturing_agent/graph/nodes/retrieve_multi.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_multi.py)
- 다중 dataset 혹은 다중 날짜 조회 경로를 담당합니다.
- 실제 병합/개요/분석 흐름은 `runtime_service` 에 위임합니다.

### [manufacturing_agent/graph/nodes/followup_analysis.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/followup_analysis.py)
- 이미 화면에 있는 `current_data` 를 재가공합니다.
- 새 raw data 조회 없이 group by, 정렬, 비율 계산 등을 처리합니다.

### [manufacturing_agent/graph/nodes/finish.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/finish.py)
- 마지막 결과를 정리합니다.
- `execution_engine` 같은 메타 정보를 찍는 위치입니다.

## `manufacturing_agent/services/`

### [manufacturing_agent/services/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/services/request_context.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/request_context.py)
- 현재 질문 주변의 문맥을 읽는 유틸 모음입니다.
- 최근 대화 텍스트, 현재 테이블 컬럼, 기존 source dataset key, 사용자 명시 필터 변경 여부 등을 계산합니다.

### [manufacturing_agent/services/parameter_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/parameter_service.py)
- 질문에서 날짜, 공정, MODE, DEN, line 등 조회 필터를 추출합니다.
- 도메인 그룹 확장, 레지스트리 값 확장, context 상속까지 같이 처리합니다.

### [manufacturing_agent/services/query_mode.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/query_mode.py)
- 현재 요청을 두 종류로 나눕니다.
- `retrieval`: 새 데이터를 가져와야 하는 경우
- `followup_transform`: 지금 테이블을 다시 가공하면 되는 경우

### [manufacturing_agent/services/retrieval_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/retrieval_planner.py)
- 어떤 dataset 조합이 필요한지 계획합니다.
- derived metric 이면 여러 raw dataset 이 모두 포함되도록 점검합니다.

### [manufacturing_agent/services/merge_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/merge_service.py)
- 여러 dataset 을 분석 가능한 하나의 테이블로 합칩니다.
- join key 선택, join cardinality 검사, many-to-many 차단이 핵심 역할입니다.

### [manufacturing_agent/services/runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)
- 실질적인 실행 총괄 계층입니다.
- retrieval, follow-up analysis, post-processing, multi-dataset merge 를 조합해 최종 결과 payload 를 만듭니다.

### [manufacturing_agent/services/response_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/response_service.py)
- 최종 자연어 응답을 생성합니다.
- 결과 미리보기와 LLM prompt 구성을 같이 담당합니다.

## `manufacturing_agent/analysis/`

### [manufacturing_agent/analysis/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/analysis/contracts.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/contracts.py)
- 분석 단계에서 오가는 데이터 구조 정의입니다.
- `RequiredParams`, `JoinRule`, `DerivedMetricRule` 같은 타입 설명서 역할을 합니다.

### [manufacturing_agent/analysis/helpers.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/helpers.py)
- DataFrame 분석을 돕는 순수 함수 모음입니다.
- 컬럼 찾기, 그룹 컬럼 찾기, top-N 파싱, fallback plan 생성 등을 처리합니다.

### [manufacturing_agent/analysis/llm_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/llm_planner.py)
- 분석용 pandas 코드 또는 계획을 LLM에 요청하는 부분입니다.
- 어떤 컬럼이 있는지, 어떤 힌트를 줄지, 어떤 JSON을 받아야 하는지 정의합니다.

### [manufacturing_agent/analysis/engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/engine.py)
- 분석의 중심 엔진입니다.
- LLM 계획, fallback 규칙, safe executor 를 연결해 실제 후처리 분석을 실행합니다.

### [manufacturing_agent/analysis/safe_executor.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/safe_executor.py)
- LLM이 만든 pandas 코드를 안전하게 검사하고 실행합니다.
- 위험한 AST 요소를 막고 `result` 출력 규칙을 강제합니다.

## `manufacturing_agent/data/`

### [manufacturing_agent/data/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)
- 현재 프로젝트의 mock 제조 데이터 생성/조회 중심 파일입니다.
- 생산, 목표, WIP, Hold, Scrap, Recipe, Lot trace 같은 dataset 함수를 모두 담고 있습니다.

## `manufacturing_agent/domain/`

### [manufacturing_agent/domain/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/domain/knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)
- 제조 도메인 상수 정의 파일입니다.
- 공정 그룹, 공정 스펙, 제품군, dataset 메타, 특수 별칭 규칙이 들어 있습니다.

### [manufacturing_agent/domain/registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/registry.py)
- 사용자 정의 도메인 규칙 저장소입니다.
- JSON 파일 로드/저장뿐 아니라, 값 확장, 분석 규칙 매칭, join rule 조회도 담당합니다.

## `manufacturing_agent/app/`

### [manufacturing_agent/app/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/app/ui_renderer.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app/ui_renderer.py)
- Streamlit 채팅 화면과 결과 렌더링을 담당합니다.
- 세션 상태 초기화, context 동기화, tool result 표시가 핵심입니다.

### [manufacturing_agent/app/ui_domain_knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app/ui_domain_knowledge.py)
- Streamlit 도메인 지식 등록 페이지입니다.
- 등록 전 미리보기, 검증, 저장 결과 표시 기능을 담고 있습니다.

## `manufacturing_agent/adapters/`

### [manufacturing_agent/adapters/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/adapters/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/adapters/langflow_nodes.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/adapters/langflow_nodes.py)
- Langflow 전환을 염두에 둔 `dict -> dict` 래퍼 모음입니다.
- LangGraph에 묶인 노드가 아니라 서비스 함수를 직접 감싸므로 재사용성이 높습니다.

## `manufacturing_agent/shared/`

### [manufacturing_agent/shared/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/shared/__init__.py)
- 패키지 마커 파일입니다.

### [manufacturing_agent/shared/config.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/shared/config.py)
- 공통 LLM 설정 파일입니다.
- 태스크별 모델 선택과 공통 시스템 프롬프트를 관리합니다.

### [manufacturing_agent/shared/filter_utils.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/shared/filter_utils.py)
- 텍스트 정규화, 키워드 포함 여부 같은 공통 문자열 유틸입니다.

### [manufacturing_agent/shared/number_format.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/shared/number_format.py)
- 수량/비율 숫자를 사람이 보기 좋게 변환하는 유틸입니다.

## `langflow_version/` Langflow 전용 폴더

### [langflow_version/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/__init__.py)
- Langflow 버전의 공개 엔트리 포인트를 export 합니다.

### [langflow_version/component_base.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/component_base.py)
- Langflow가 없는 로컬 환경에서도 import/test 가능하게 만드는 호환 레이어입니다.
- 실제 Langflow 클래스가 있으면 그것을 쓰고, 없으면 fallback 클래스를 씁니다.

### [langflow_version/workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)
- LangGraph 런타임 없이도 같은 흐름을 따라 실행하는 순수 파이썬 워크플로우입니다.
- Langflow 컴포넌트가 공통으로 호출하는 실행 코어입니다.

### [langflow_version/components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)
- Langflow 커스텀 컴포넌트 클래스 모음입니다.
- 전체 실행용 컴포넌트와 단계별 컴포넌트를 모두 제공합니다.

## `core/` 레거시/호환 계층

중요:

- 실제 v2 학습은 `manufacturing_agent/` 부터 시작하는 것을 권장합니다.
- `core/` 는 기존 구조를 참고하거나 이전 import 경로를 유지하기 위한 폴더입니다.

### [core/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/__init__.py)
- `run_agent` 를 외부에 노출하는 호환 지점입니다.

### [core/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/agent.py)
- 가장 중요한 호환 래퍼입니다.
- 실제 구현은 `manufacturing_agent.agent.run_agent` 로 넘깁니다.

### [core/analysis_contracts.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/analysis_contracts.py)
- 예전 구조의 타입 정의 파일입니다.
- 개념상 `manufacturing_agent.analysis.contracts` 와 대응됩니다.

### [core/analysis_helpers.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/analysis_helpers.py)
- 예전 구조의 분석 보조 함수 파일입니다.

### [core/analysis_llm.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/analysis_llm.py)
- 예전 구조의 분석 LLM planner 파일입니다.

### [core/config.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/config.py)
- 예전 구조의 공통 설정 파일입니다.

### [core/data_analysis_engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/data_analysis_engine.py)
- 예전 구조의 분석 엔진 파일입니다.

### [core/data_tools.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/data_tools.py)
- 예전 구조의 dataset retrieval/mock data 파일입니다.

### [core/domain_knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/domain_knowledge.py)
- 예전 구조의 도메인 상수 파일입니다.

### [core/domain_registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/domain_registry.py)
- 예전 구조의 사용자 규칙 레지스트리 파일입니다.

### [core/filter_utils.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/filter_utils.py)
- 예전 구조의 문자열 필터 유틸입니다.

### [core/number_format.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/number_format.py)
- 예전 구조의 숫자 표시 유틸입니다.

### [core/parameter_resolver.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/parameter_resolver.py)
- 예전 구조의 파라미터 추출 파일입니다.

### [core/safe_code_executor.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/safe_code_executor.py)
- 예전 구조의 안전 실행기입니다.

## Scripts And Tests

### [scripts/run_validation_scenarios.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/scripts/run_validation_scenarios.py)
- 여러 질문 시나리오를 한 번에 점검하는 수동 검증용 스크립트입니다.

### [tests/conftest.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/tests/conftest.py)
- 테스트 실행 시 프로젝트 루트를 import path 에 넣는 설정입니다.

### [tests/test_v2_structure.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/tests/test_v2_structure.py)
- v2 구조, 기본 파라미터 추출, Langflow adapter, smoke 실행을 검증하는 테스트 파일입니다.
