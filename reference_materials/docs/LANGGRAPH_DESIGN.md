# LangGraph 구조 안내

이 문서는 LangGraph 버전의 실행 구조를 설명합니다.  
기본 버전과 기능은 비슷하지만, 내부 흐름을 `StateGraph` 노드로 나눠 처리한다는 점이 핵심입니다.

## 1. 왜 LangGraph로 나눴는가

기존 함수형 흐름도 충분히 동작하지만, 아래 이유 때문에 LangGraph 구조가 도움이 됩니다.

- 단계별 책임을 더 명확하게 나눌 수 있습니다.
- 중간 상태를 관리하기 쉽습니다.
- 나중에 검증 노드, 사람 확인 노드, DB 전용 노드 같은 확장이 쉬워집니다.
- 조회와 분석이 복잡해질수록 라우팅 구조를 더 안정적으로 표현할 수 있습니다.

## 2. 현재 그래프 흐름

현재 `run_agent()`가 호출되면 그래프는 대략 아래 순서로 흐릅니다.

```text
resolve_request
  -> plan_retrieval 또는 followup_analysis
  -> single_retrieval 또는 multi_retrieval
  -> finish
```

## 3. 노드별 역할

### `resolve_request`

역할:

- 질문에서 날짜, 공정, MODE 같은 파라미터를 추출합니다.
- 새 조회인지, 현재 결과 기준 후속 분석인지 판단합니다.

입력:

- 사용자 질문
- 현재 세션 데이터
- 최근 대화 맥락

출력:

- 정리된 파라미터
- query mode

### `plan_retrieval`

역할:

- 어떤 데이터셋을 불러와야 하는지 계획합니다.
- 복수 데이터셋이 필요한지 판단합니다.
- 등록된 `analysis_rules`를 보고 필요한 데이터셋을 보강합니다.

예:

- `생산량` -> `production`
- `생산 달성률` -> `production + target`
- `홀드 부하지수` -> `hold + production`
- `설비재공 복합이상여부` -> `equipment + wip`

### `single_retrieval`

역할:

- 하나의 조회 job을 실행합니다.
- 필요하면 후처리까지 이어집니다.

언제 쓰나:

- 단일 데이터셋 조회
- 첫 질문이지만 한 데이터셋만으로 답할 수 있는 경우

### `multi_retrieval`

역할:

- 여러 데이터셋을 함께 조회합니다.
- 같은 데이터셋을 날짜별로 여러 번 조회할 수도 있습니다.

언제 쓰나:

- `생산과 목표 같이 보여줘`
- `어제와 오늘 생산 비교해줘`
- 사용자 등록 계산 규칙이 복수 테이블을 요구할 때

### `followup_analysis`

역할:

- 이미 화면에 있는 `current_data`를 다시 가공합니다.

예:

- `MODE별로 묶어줘`
- `상위 5개만 보여줘`
- `오름차순으로 정렬해줘`

### `finish`

역할:

- 최종 응답 payload를 UI가 받기 좋은 형태로 정리합니다.
- 현재 결과와 tool 결과 목록을 마무리합니다.

## 4. 도메인 관리 기능은 어디에 붙는가

LangGraph 버전에서도 도메인 등록은 별도 UI로 들어오지만, 실제 반영은 그래프 여러 단계에 퍼져 있습니다.

### `core/domain_registry.py`

- 줄글을 구조화합니다.
- JSON 파일로 저장/삭제합니다.
- 실행용 프롬프트 텍스트를 만듭니다.

### `plan_retrieval`

- `analysis_rules.required_datasets`를 보고 필요한 데이터셋을 더 불러오게 만듭니다.

### `parameter_resolver`

- `value_groups`를 보고 별칭을 실제 필터 값으로 확장합니다.

### `analysis_llm`

- `source_columns`, `calculation_mode`, `condition`, `decision_rule`, `output_column`을 보고 pandas 코드 생성 힌트를 강화합니다.

즉, 도메인 등록은 그래프 바깥 기능이 아니라 그래프 내부 의사결정에도 직접 연결됩니다.

## 5. 현재 도메인 등록이 지원하는 범위

### 데이터셋 표현 등록

예:

```text
양품률이라는 표현은 수율 데이터셋을 뜻해.
```

### 필터 별칭 등록

예:

```text
후공정A는 D/A1, D/A2를 뜻해.
```

### 계산 규칙 등록

예:

```text
홀드 부하지수는 hold 테이블의 hold_qty 와 production 테이블의 production 을 같이 가져와서
hold_qty / production 으로 계산해줘.
```

### 판정 규칙 등록

예:

```text
HOLD 이상여부는 wip 테이블의 상태 컬럼이 HOLD, REWORK, WAIT_MATERIAL 중 하나이면 이상,
아니면 정상으로 판단해줘.
```

### 삭제 기능

- `도메인 관리 > 목록`에서 엔트리별 삭제

## 6. LangGraph 구조에서 확장하기 쉬운 방향

이 구조는 앞으로 아래 같은 확장에 유리합니다.

- Oracle 실제 조회 전용 노드 추가
- 검증 전용 노드 추가
- 사람이 확인하는 approval 노드 추가
- 도메인 규칙 추천/검토 노드 추가
- 응답 생성과 분석 생성 노드 분리

## 7. 한 줄 요약

LangGraph 버전은 "질문 해석 -> 조회 계획 -> 단일/복수 조회 -> 후처리 -> 마무리"를 노드로 명확히 분리한 버전이며, 최근 추가된 도메인 등록/계산 규칙/삭제 기능도 이 그래프 흐름 안에 자연스럽게 연결되어 있습니다.
