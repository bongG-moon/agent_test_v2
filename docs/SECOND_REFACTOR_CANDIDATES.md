# Second Refactor Candidates

이 문서는 현재 구조에서 기능은 유지하면서도 복잡도를 한 번 더 낮출 수 있는 지점을 우선순위별로 정리한 문서입니다.

전제:

- 제조 도메인 의미는 유지
- 현재 기능은 유지
- LangGraph 버전과 Langflow 버전은 계속 공통 코어를 공유
- “초보자가 읽기 쉬운 구조”를 더 강화

## 먼저 결론

지금 기준으로 가장 복잡도가 높은 지점은 아래 5곳입니다.

1. [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)
2. [manufacturing_agent/domain/registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/registry.py)
3. [manufacturing_agent/domain/knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)
4. [manufacturing_agent/services/parameter_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/parameter_service.py)
5. [manufacturing_agent/services/merge_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/merge_service.py)

그다음 후보는 아래입니다.

6. [manufacturing_agent/services/runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)
7. [manufacturing_agent/analysis/engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/engine.py)
8. [manufacturing_agent/services/retrieval_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/retrieval_planner.py)

## 왜 이 파일들이 복잡한가

현재 대략적인 파일 크기:

- `data/retrieval.py`: 약 720줄
- `domain/registry.py`: 약 673줄
- `domain/knowledge.py`: 약 571줄
- `parameter_service.py`: 약 478줄
- `merge_service.py`: 약 437줄
- `runtime_service.py`: 약 322줄
- `analysis/engine.py`: 약 312줄
- `retrieval_planner.py`: 약 285줄

파일이 길다는 것 자체보다, “한 파일 안에 서로 다른 책임이 같이 섞여 있다”는 점이 더 큰 원인입니다.

## 우선순위 A: 가장 먼저 줄이면 좋은 곳

### 1. `data/retrieval.py`

왜 복잡한가:

- dataset registry
- 공통 필터 처리
- mock row 생성
- dataset별 생성 함수
- tool 실행기

이 5개 책임이 한 파일에 같이 있습니다.

추천 분리:

1. `data/catalog.py`
   - dataset label, registry, dataset_requires_date, pick_retrieval_tools
2. `data/common_filters.py`
   - `_as_list`, `_normalize_key`, `_apply_common_filters`, 제품 매칭 함수
3. `data/mock_builders.py`
   - `_build_base_row`, `_pick_equipment`, `_apply_signal_overrides`
4. `data/datasets/*.py`
   - production, target, wip, yield, hold, scrap, recipe, lot_trace
5. `data/executor.py`
   - `execute_retrieval_tools`, `build_current_datasets`

단순화 효과:

- 새 dataset 추가가 쉬워집니다.
- 초보자가 “공통 로직”과 “dataset별 로직”을 구분하기 쉬워집니다.

### 2. `domain/registry.py`

왜 복잡한가:

- 파일 저장
- JSON normalize
- LLM text parsing
- builtin rule 생성
- 검색/확장/매칭

이 기능들이 모두 한 파일에 있습니다.

추천 분리:

1. `domain/registry_storage.py`
   - load/save/delete/list
2. `domain/registry_normalizers.py`
   - `_normalize_*` 함수들
3. `domain/registry_parser.py`
   - text -> payload 추론, LLM parsing
4. `domain/registry_matchers.py`
   - expand/detect/match 함수들
5. `domain/registry_defaults.py`
   - builtin value groups, builtin dataset keywords, default rules

단순화 효과:

- 저장 계층과 rule 해석 계층이 분리됩니다.
- 테스트도 훨씬 잘게 나눌 수 있습니다.

### 3. `domain/knowledge.py`

왜 복잡한가:

- 상수 정의 파일인데 너무 많은 종류의 상수가 한 파일에 모여 있습니다.
- 공정, 제품, dataset metadata, alias rule 이 한 덩어리입니다.

추천 분리:

1. `domain/process_catalog.py`
2. `domain/product_catalog.py`
3. `domain/dataset_catalog.py`
4. `domain/knowledge_prompt.py`

단순화 효과:

- 도메인 데이터 자체가 더 읽기 쉬워집니다.
- 초보자도 “공정 정보는 여기”, “제품 정보는 여기”라고 바로 찾을 수 있습니다.

## 우선순위 B: 그 다음에 줄이면 좋은 곳

### 4. `parameter_service.py`

왜 복잡한가:

- LLM 추출
- context 상속
- 날짜 fallback
- 그룹 확장
- 도메인 override

이 흐름이 한 파일 안에서 길게 이어집니다.

추천 분리:

1. `services/parameter_llm.py`
   - LLM prompt, JSON parsing
2. `services/parameter_inheritance.py`
   - context 상속
3. `services/parameter_detectors.py`
   - oper_num, pkg, special product 감지
4. `services/parameter_normalizers.py`
   - group canonicalize, merge helper
5. `services/parameter_service.py`
   - 최종 조립만 담당

단순화 효과:

- 메인 함수 `resolve_required_params()` 가 훨씬 짧아집니다.
- 디버깅 포인트가 명확해집니다.

### 5. `merge_service.py`

왜 복잡한가:

- join key 선택
- cardinality 판정
- join rule 적용
- merge 실행
- overview 생성

이 중 “join planning”과 “merge execution”이 사실상 다른 책임입니다.

추천 분리:

1. `services/join_planner.py`
   - join key, join type, cardinality 관련 함수
2. `services/merge_executor.py`
   - 실제 pandas merge 와 cleanup
3. `services/merge_service.py`
   - 최상위 orchestration 만 담당

단순화 효과:

- many-to-many 방지 로직을 따로 이해할 수 있습니다.
- merge bug가 날 때 찾기 쉬워집니다.

## 우선순위 C: 구조는 좋지만 아직 무거운 곳

### 6. `runtime_service.py`

왜 복잡한가:

- single retrieval
- multi retrieval
- follow-up analysis
- post-processing retry

이 4가지 실행 패턴이 한 파일에 모여 있습니다.

추천 분리:

1. `services/runtime_single.py`
2. `services/runtime_multi.py`
3. `services/runtime_followup.py`
4. `services/runtime_shared.py`

유지할 점:

- 지금도 graph node 가 얇다는 장점은 좋습니다.
- 그래서 이 파일은 완전 재설계보다 하위 모듈 분리가 더 적절합니다.

### 7. `analysis/engine.py`

왜 복잡한가:

- 계획 수립
- fallback 계산
- 재시도
- 결과 payload 생성

추천 분리:

1. `analysis/execution_result.py`
2. `analysis/fallback_rules.py`
3. `analysis/retry_logic.py`
4. `analysis/engine.py`

### 8. `retrieval_planner.py`

왜 복잡한가:

- planning
- sufficiency review
- date slice
- job 생성
- execution helper

추천 분리:

1. `services/retrieval_plan_llm.py`
2. `services/retrieval_job_builder.py`
3. `services/retrieval_review.py`
4. `services/retrieval_planner.py`

## 초보자 관점에서 가장 체감 큰 개선 순서

초보자 가독성만 기준으로 보면 이 순서가 제일 좋습니다.

1. `domain/knowledge.py` 분리
2. `data/retrieval.py` 분리
3. `parameter_service.py` 분리
4. `merge_service.py` 분리
5. `domain/registry.py` 분리

이 순서가 좋은 이유:

- 먼저 “읽기 쉬운 상수/데이터 파일”이 분리되면 전체 진입 장벽이 내려갑니다.
- 그 다음에 계산 로직을 분리하면 함수 호출 흐름도 같이 쉬워집니다.

## Langflow 관점에서 더 단순화할 포인트

Langflow 전환을 더 쉽게 하려면 아래 기준이 좋습니다.

1. 각 서비스 모듈의 공개 함수는 `입력 dict 1개 -> 출력 dict 1개` 형태로 더 맞추기
2. 상태 변경 함수와 계산 함수를 분리하기
3. `runtime_service` 내부 branch 로직을 더 작게 쪼개기
4. Langflow 컴포넌트가 직접 참조하는 함수 이름을 안정적으로 고정하기

추천 추가 래퍼:

- `services/public_api.py`
  - LangGraph, Langflow, 테스트가 공통으로 부를 공개 함수만 모으기

## 지금 당장 손대지 않는 것이 좋은 곳

아래는 복잡해 보여도 당장 크게 흔들지 않는 것이 좋습니다.

### `graph/`

이유:

- 현재는 이미 충분히 얇습니다.
- 복잡함의 원인이 graph가 아니라 service 내부에 있습니다.

### `langflow_version/components.py`

이유:

- 현재 크기가 크지 않습니다.
- 코어가 더 정리된 뒤 따라가서 정리하는 편이 안전합니다.

### `app/ui_renderer.py`

이유:

- UI 특성상 조건 분기가 어느 정도 많은 것은 자연스럽습니다.
- 지금은 코어 구조 단순화가 우선입니다.

## 추천 실행 계획

기능 유지 전제로 2차 리팩터링을 한다면 이 순서를 권장합니다.

### Phase 1

- `domain/knowledge.py` 분리
- `data/retrieval.py` 분리

### Phase 2

- `parameter_service.py` 분리
- `merge_service.py` 분리

### Phase 3

- `domain/registry.py` 분리
- `runtime_service.py` 분리
- `analysis/engine.py` 보조 모듈 분리

## 성공 기준

2차 단순화가 잘 됐다고 볼 수 있는 기준:

1. 초보자가 파일 이름만 보고 역할을 추정할 수 있다.
2. 한 파일 안에 책임이 2개 이상 섞이지 않는다.
3. 공개 진입 함수가 파일마다 1~3개 수준으로 줄어든다.
4. dataset 추가, join rule 수정, 파라미터 규칙 수정 위치를 바로 찾을 수 있다.

## 같이 보면 좋은 문서

- [START_HERE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/START_HERE.md)
- [PYTHON_FILE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/PYTHON_FILE_GUIDE.md)
- [FUNCTION_ROLE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/FUNCTION_ROLE_GUIDE.md)
- [LANGFLOW_VERSION.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_VERSION.md)
