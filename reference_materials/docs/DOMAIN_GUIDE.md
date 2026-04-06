# 도메인 가이드

이 문서는 이 프로젝트가 도메인 지식을 어떻게 저장하고, 어떻게 실행에 반영하는지 설명합니다.  
특히 `도메인 관리` 화면에서 무엇을 넣을 수 있는지 초보자도 이해할 수 있도록 자세히 정리했습니다.

## 1. 도메인 지식이 필요한 이유

사용자는 항상 시스템이 아는 정식 표현만 쓰지 않습니다.

예를 들면:

- `DA공정`
- `후공정A`
- `양품률`
- `고용량 제품`
- `생산 달성률`
- `HOLD 이상여부`

이런 표현은 질문으로는 자연스럽지만, 시스템이 정확히 동작하려면 아래를 알아야 합니다.

- 어떤 데이터셋을 불러와야 하는가
- 어떤 필터 값으로 바꿔야 하는가
- 어떤 계산식이나 판정 로직을 적용해야 하는가

이 정보를 관리하는 곳이 도메인 지식입니다.

## 2. 도메인 지식은 두 종류다

### 기본 도메인 지식

코드에 포함된 고정 정보입니다.

- 위치: [`core/domain_knowledge.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/domain_knowledge.py)

포함 내용 예:

- 공정 그룹
- MODE, DEN, TECH, PKG 분류
- 기본 데이터셋 키워드
- 기본 분석 규칙

### 사용자 등록 도메인 지식

도메인 관리 화면에서 사용자가 추가한 정보입니다.

- 위치: [`reference_materials/domain_registry/entries`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/domain_registry/entries)

현재는 DB가 아니라 JSON 파일 기반입니다.

## 3. 사용자 등록 도메인은 어떤 형태로 저장되나

사용자가 줄글을 넣으면 LLM이 아래 구조로 바꿉니다.

### 1. `dataset_keywords`

질문 표현과 데이터셋의 연결입니다.

예:

- `양품률 -> yield`
- `불량비용 -> scrap`

이 정보는 질문에서 어떤 데이터셋을 선택할지 판단할 때 사용됩니다.

### 2. `value_groups`

별칭을 실제 필터 값 목록으로 확장하는 정보입니다.

예:

- `후공정A -> D/A1, D/A2`
- `고용량 제품 -> 512G, 1T`

이 정보는 파라미터 추출 뒤 실제 필터 값으로 확장할 때 사용됩니다.

### 3. `analysis_rules`

계산 규칙이나 판정 규칙입니다.

이제 이 프로젝트는 단순 별칭만이 아니라, 계산/판정 로직도 줄글로 등록할 수 있습니다.

예:

- `생산 달성률 = production / target`
- `홀드 부하지수 = hold_qty / production`
- `HOLD 이상여부 = 상태가 HOLD, REWORK면 이상`
- `장비 가동 이상여부 = 가동률이 85 미만이면 이상`

### 4. `notes`

구조화하기 어려운 참고 문장을 보관하는 메모입니다.

## 4. 분석 규칙은 어떤 필드를 가지나

계산/판정 규칙은 `analysis_rules`로 저장됩니다.  
아래 필드들을 이해하면 동작 구조를 훨씬 쉽게 볼 수 있습니다.

- `name`
  - 내부 식별용 이름입니다.
  - 보통 영문 snake_case를 추천합니다.
- `display_name`
  - 화면과 프롬프트에 보일 사람이 읽는 이름입니다.
- `synonyms`
  - 사용자가 실제 질문에서 쓸 표현 목록입니다.
- `required_datasets`
  - 이 규칙을 계산하기 위해 필요한 데이터셋 목록입니다.
- `required_columns`
  - 필요한 주요 컬럼 목록입니다.
- `source_columns`
  - 어떤 데이터셋의 어떤 컬럼을 어떤 역할로 쓰는지 설명합니다.
  - 예: `production:numerator`, `target:denominator`
- `calculation_mode`
  - 규칙의 성격입니다.
  - 예: `ratio`, `condition_flag`, `threshold_flag`
- `output_column`
  - 결과 컬럼 이름입니다.
- `default_group_by`
  - 사용자가 별도 요청을 하지 않았을 때 기본 집계 기준입니다.
- `condition`
  - 조건 판정이 필요한 경우 논리 조건을 적습니다.
- `decision_rule`
  - 조건이 참일 때 어떤 값을 내야 하는지 설명합니다.
- `formula`
  - 계산식 설명입니다.
- `pandas_hint`
  - pandas 코드 생성 시 참고할 힌트입니다.

## 5. 실제 등록 예시

### 데이터셋 키워드 예시

```text
양품률이라는 표현은 수율 데이터셋을 뜻해.
불량비용이라는 표현은 scrap 데이터셋을 뜻해.
```

### 필터 별칭 예시

```text
후공정A는 D/A1, D/A2를 뜻해.
고용량 제품은 DEN 기준으로 512G, 1T를 의미해.
```

### 계산 규칙 예시

```text
생산 달성율은 production 테이블의 production 값과 target 테이블의 target 값을 가져와서
production / target 으로 계산해줘.
결과 컬럼 이름은 achievement_rate 로 해줘.
```

```text
홀드 부하지수는 hold 테이블의 hold_qty 와 production 테이블의 production 을 같이 가져와서
hold_qty / production 으로 계산해줘.
```

### 판정 규칙 예시

```text
HOLD 이상여부는 wip 테이블의 상태 컬럼이 HOLD, REWORK, WAIT_MATERIAL 중 하나이면 이상,
아니면 정상으로 판단해줘.
```

```text
설비재공 복합이상여부는 equipment 테이블의 가동률과 wip 테이블의 재공수량을 같이 보고,
가동률이 85 미만이면서 재공수량이 1800 이상이면 이상, 아니면 정상으로 판단해줘.
```

## 6. 도메인 등록은 어디에 반영되나

### `core/data_tools.py`

등록된 `dataset_keywords`를 보고 질문에 맞는 데이터셋을 선택합니다.

### `core/parameter_resolver.py`

등록된 `value_groups`를 보고 별칭을 실제 필터 값 목록으로 확장합니다.

### `core/agent.py`

등록된 `analysis_rules`를 보고 필요한 데이터셋 조합을 보강합니다.

예를 들어 `생산 달성률` 규칙이 있으면:

- 생산만 조회하고 끝나지 않고
- `production + target`을 함께 불러오도록 계획할 수 있습니다.

### `core/analysis_llm.py`

등록된 `analysis_rules`의 계산식, 조건, 판정 힌트를 pandas 코드 생성 프롬프트에 넣습니다.

즉, 등록된 규칙은 실제 분석 코드 생성에 직접 영향을 줍니다.

## 7. 등록 전에 왜 미리보기를 해야 하나

등록 화면의 `미리보기`는 아주 중요합니다.  
이 단계에서 아래를 확인할 수 있기 때문입니다.

- LLM이 내 문장을 원하는 구조로 잘 해석했는지
- 기존 의미와 중복되거나 충돌하지 않는지
- 위험한 표현이 들어가 있지 않은지

## 8. 중복과 충돌은 어떻게 검사하나

검사는 [`core/domain_registry.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/domain_registry.py) 의 `validate_domain_payload()`가 담당합니다.

주요 검사 항목:

- 같은 keyword가 다른 데이터셋과 충돌하는지
- 같은 별칭이 다른 값 그룹과 충돌하는지
- 같은 분석 규칙 이름/별칭이 다른 의미로 겹치는지
- unsafe text가 포함되어 있는지
- 계산 규칙인데 필요한 `source_columns`, `condition`, `output_column`이 너무 비어 있지는 않은지

검사 결과는 두 종류입니다.

- `warning`
  - 저장은 가능하지만 확인이 필요한 경우
- `error`
  - 실제 충돌이나 위험 요소가 있어 저장하면 안 되는 경우

## 9. 등록된 엔트리를 삭제할 수 있나

가능합니다.

`도메인 관리 > 목록`에서 각 엔트리마다 `삭제` 버튼이 있습니다.  
삭제하면 해당 엔트리 JSON 파일이 실제로 제거됩니다.

이 기능은 다음 상황에서 유용합니다.

- 실수로 잘못 등록한 경우
- 테스트용 엔트리를 지우고 싶은 경우
- 같은 의미를 더 좋은 문장으로 다시 등록하고 싶은 경우

## 10. 일반 사용자와 개발자는 어디까지 다르게 보아야 하나

### 일반 사용자

보통은 `도메인 관리` 화면만 사용하면 충분합니다.

추천 작업:

- 새 표현 추가
- 새 별칭 그룹 추가
- 계산 규칙 추가
- 판정 규칙 추가
- 목록에서 확인/삭제

### 개발자

기본 구조 자체를 바꾸는 경우에만 코드 수정이 필요합니다.

예:

- 새로운 기본 데이터셋 추가
- 기본 공정 그룹 수정
- mock 데이터 구조 자체 변경
- 기본 내장 규칙 추가

## 11. 한 줄 요약

이 프로젝트의 도메인 등록 기능은 단순 메모 저장이 아닙니다.  
질문 해석, 데이터셋 선택, 필터 확장, 파생 지표 계산, pandas 코드 생성까지 연결되는 실행용 지식 관리 기능입니다.
