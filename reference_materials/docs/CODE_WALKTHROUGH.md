# 코드 상세 안내

이 문서는 LangGraph 버전 코드를 초보자도 따라가며 이해할 수 있도록 만든 문서입니다.  
기본 기능은 기존 버전과 비슷하지만, 실행 방식은 `StateGraph` 기반이라는 점이 가장 큰 차이입니다.

## 1. 전체 흐름 한눈에 보기

```text
app.py
  -> 화면 선택
     -> 채팅 분석 화면
        -> core/agent.py::run_agent()
           -> StateGraph 실행
              -> resolve_request
              -> plan_retrieval 또는 followup_analysis
              -> single_retrieval 또는 multi_retrieval
              -> finish
        -> ui_renderer.py
     -> 도메인 관리 화면
        -> ui_domain_knowledge.py
        -> core/domain_registry.py
```

## 2. `app.py`

[`app.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/app.py)는 Streamlit 진입점입니다.

역할:

- 세션 상태 초기화
- 화면 전환
- 채팅 턴 실행
- 상태 박스와 답변 출력

사용자 입장에서는 기본 버전과 거의 비슷하게 보이지만, 내부적으로는 `run_agent()`가 LangGraph를 실행합니다.

## 3. `ui_domain_knowledge.py`

[`ui_domain_knowledge.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/ui_domain_knowledge.py)는 도메인 관리 페이지 UI입니다.

여기서 하는 일:

- 등록 탭 렌더링
- 예시 문구 표시
- 미리보기/등록 처리
- 목록 렌더링
- 삭제 버튼 처리

실제 저장과 삭제는 이 파일이 아니라 `core/domain_registry.py`가 맡습니다.

## 4. `core/domain_registry.py`

[`core/domain_registry.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/domain_registry.py)는 사용자 등록 도메인의 중심입니다.

주요 역할:

- 사용자 등록 엔트리 로드
- 줄글을 구조화
- 중복/충돌/위험 표현 검사
- JSON 저장
- JSON 삭제
- 실행용 프롬프트 텍스트 생성

중요 함수:

- `load_domain_registry()`
- `parse_domain_text_to_payload()`
- `preview_domain_submission()`
- `register_domain_submission()`
- `delete_domain_entry()`
- `get_dataset_keyword_map()`
- `match_registered_analysis_rules()`
- `build_registered_domain_prompt()`

## 5. `core/agent.py`

[`core/agent.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/agent.py)는 LangGraph 오케스트레이터입니다.

이 파일에는:

- 상태 구조
- 노드 함수
- 라우팅
- 그래프 구성

이 들어 있습니다.

### 주요 노드

#### `resolve_request`

- 질문에서 파라미터를 추출합니다.
- 새 조회인지, 후속 분석인지 판단합니다.

#### `plan_retrieval`

- 어떤 데이터셋이 필요한지 계획합니다.
- 등록된 `analysis_rules`를 보고 필요한 데이터셋을 보강할 수 있습니다.

예:

- `달성률` -> `production + target`
- 사용자 규칙 `hold_load_index` -> `hold + production`

#### `single_retrieval`

- 하나의 조회 job을 처리합니다.
- 필요하면 후처리까지 바로 이어집니다.

#### `multi_retrieval`

- 여러 데이터셋을 함께 조회하거나
- 같은 데이터셋을 날짜별로 반복 조회하는 경우를 처리합니다.

#### `followup_analysis`

- 현재 결과 표를 다시 가공합니다.

#### `finish`

- UI가 받기 좋은 최종 payload를 정리합니다.

## 6. `core/parameter_resolver.py`

[`core/parameter_resolver.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/parameter_resolver.py)는 질문에서 조건을 뽑습니다.

예:

- 날짜
- 공정
- MODE
- DEN
- PKG
- MCP_NO

등록 도메인과의 연결:

- `value_groups`를 보고 별칭을 실제 값 목록으로 확장합니다.

## 7. `core/data_tools.py`

[`core/data_tools.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/data_tools.py)는 조회 레이어입니다.

역할:

- 데이터셋 registry 관리
- 데이터셋 선택
- mock 데이터 생성
- 공통 필터 적용

등록 도메인과의 연결:

- `dataset_keywords`를 함께 반영해 데이터셋 선택 정확도를 높입니다.

## 8. `core/data_analysis_engine.py`

[`core/data_analysis_engine.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/data_analysis_engine.py)는 pandas 후처리 실행기입니다.

처리 순서:

1. 현재 데이터 확인
2. 필요한 컬럼 확인
3. LLM에게 pandas 계획 요청
4. 코드 검증
5. 안전 실행
6. 필요 시 재시도
7. 그래도 실패하면 최소 fallback

## 9. `core/analysis_llm.py`

[`core/analysis_llm.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/analysis_llm.py)는 pandas 코드 생성 프롬프트를 만듭니다.

최근 중요한 점:

- 등록된 `analysis_rules`를 더 풍부하게 프롬프트에 넣습니다.
- `source_columns`, `calculation_mode`, `condition`, `decision_rule`, `output_column` 같은 정보까지 전달합니다.

즉, 사용자가 도메인 관리 화면에서 줄글로 등록한 계산/판정 규칙이 실제 pandas 코드 생성 힌트로 연결됩니다.

## 10. 저장 구조는 어떻게 생겼나

### 기본 도메인 지식

- [`core/domain_knowledge.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/domain_knowledge.py)

### 사용자 등록 도메인

- [`reference_materials/domain_registry/entries`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/domain_registry/entries)

엔트리 1개 = JSON 파일 1개입니다.  
삭제 기능은 해당 JSON 파일 1개를 제거하는 방식입니다.

## 11. 문제를 볼 때 어디부터 보면 좋은가

### 질문 해석이 이상하다

1. [`core/parameter_resolver.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/parameter_resolver.py)
2. [`core/domain_knowledge.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/domain_knowledge.py)
3. [`core/domain_registry.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/domain_registry.py)

### 잘못된 데이터셋을 불러온다

1. [`core/agent.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/agent.py)
2. [`core/data_tools.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/data_tools.py)
3. [`core/domain_registry.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/domain_registry.py)

### 계산 로직이 반영되지 않는다

1. [`core/domain_registry.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/domain_registry.py)
2. [`core/agent.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/agent.py)
3. [`core/analysis_llm.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/analysis_llm.py)
4. [`core/data_analysis_engine.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/data_analysis_engine.py)

## 12. 한 줄 요약

LangGraph 버전은 기능 자체보다 실행 구조가 다른 버전입니다.  
초보자라면 먼저 `app.py`, `ui_domain_knowledge.py`, `core/domain_registry.py`, `core/agent.py` 네 파일을 순서대로 보는 것이 가장 이해하기 쉽습니다.
