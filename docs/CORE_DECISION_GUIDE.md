# Core Decision Guide

이 문서는 `core/` 폴더를 앞으로 어떻게 다루면 좋은지 정리한 기준서입니다.

결론부터 말하면:

- 지금은 `core/` 를 완전히 지우기보다 “호환 레이어”로 두는 것이 안전합니다.
- 하지만 새 기능은 `core/` 에 추가하지 않는 것이 좋습니다.
- 장기적으로는 `core/` 를 더 얇게 만들고, 최종적으로는 제거 가능한 상태를 목표로 하면 됩니다.

## 왜 `core/` 를 바로 지우지 않았는가

이유는 3가지입니다.

1. 기존 import 경로를 쓰는 코드가 있을 수 있습니다.
2. 과거 구조와 새 구조를 비교하며 이해해야 할 수도 있습니다.
3. 한번에 완전 제거하면 회귀 위험이 커집니다.

## 지금 `core/` 의 역할

현재 기준으로 `core/` 는 2가지 역할만 가져가는 것이 좋습니다.

1. 이전 import 경로 호환
2. 과거 구조 참조

예를 들면 [core/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core/agent.py) 는 실제 구현이 아니라 [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py) 로 넘기는 래퍼 역할입니다.

## 앞으로의 기준

### `core/` 에 남겨도 되는 것

- 단순 import forwarding
- deprecated 경고를 붙이기 위한 얇은 래퍼
- 이전 사용자 코드가 깨지지 않게 하는 최소 호환 지점

### `core/` 에 더 넣지 말아야 하는 것

- 새로운 비즈니스 로직
- 새로운 도메인 규칙
- 새로운 dataset 생성 코드
- Langflow 전용 로직
- 복잡한 분석 로직

## 새 기능을 어디에 넣어야 하나

기능별 기준은 이렇게 잡으면 됩니다.

- 실행 흐름 변경
  - `manufacturing_agent/graph/`
- 실제 판단/계산 로직
  - `manufacturing_agent/services/`
- 분석 관련
  - `manufacturing_agent/analysis/`
- 도메인 규칙/지식
  - `manufacturing_agent/domain/`
- mock dataset/retrieval
  - `manufacturing_agent/data/`
- Langflow 전용 연결
  - `langflow_version/`

## `core/` 를 유지할지 줄일지 판단하는 질문

아래 질문에 답해보면 됩니다.

1. 이 파일이 단순 호환용인가?
2. 이 파일 없이도 새 구조만으로 기능 설명이 가능한가?
3. 외부 코드가 아직 이 파일 경로를 사용할 가능성이 있는가?
4. 이 파일이 초보자 이해를 방해하는가?

권장 판단:

- `1번 예`, `3번 예` 이면 잠시 유지
- `2번 예`, `4번 예` 이고 외부 의존이 없으면 제거 후보

## 추천 단계별 전략

### 단계 1: 현재

- `core/` 유지
- 새 기능은 추가하지 않음
- 문서에서 “실제 구현은 manufacturing_agent” 라고 명시

### 단계 2: 점진적 축소

- `core/agent.py` 같은 파일만 남기고 나머지는 더 얇은 래퍼로 바꾸기
- 내부 구현이 중복된 파일은 순차적으로 제거 검토

### 단계 3: 최종 정리

- 외부 의존이 없다고 확인되면 `core/` 제거
- 또는 `core/compat/` 처럼 이름을 바꿔 의도를 더 분명히 하기

## 초보자 관점에서의 권장 정책

초보자가 헷갈리지 않게 하려면 아래 원칙이 좋습니다.

1. 문서에서 `manufacturing_agent/` 가 실제 코드라고 계속 강조
2. `core/` 는 “읽지 않아도 되는 폴더”로 명확히 표시
3. 새 예제, 새 테스트, 새 설명은 모두 `manufacturing_agent/` 기준으로 작성

## 실무적으로 가장 안전한 운영안

지금 프로젝트에는 이 운영안이 가장 현실적입니다.

1. `core/` 는 유지
2. 새 개발은 `manufacturing_agent/` 와 `langflow_version/` 에만 진행
3. 문서와 테스트도 새 구조 기준으로만 확장
4. 일정 시간이 지난 뒤 실제 외부 의존을 확인하고 제거 여부 결정

## 같이 보면 좋은 문서

- [docs/START_HERE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/START_HERE.md)
- [docs/PYTHON_FILE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/PYTHON_FILE_GUIDE.md)
- [docs/FUNCTION_ROLE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/FUNCTION_ROLE_GUIDE.md)
