# Core Decision Guide

이 문서는 과거 `core/` 폴더를 제거한 뒤, 어떤 기준으로 새 구조를 유지하면 좋은지 정리한 문서입니다.

결론부터 말하면:

- 현재 저장소에서는 `core/` 가 제거되었습니다.
- 새 기준은 `manufacturing_agent/` 와 `langflow_version/` 중심입니다.
- 앞으로는 과거 구조를 다시 되살리기보다 새 구조를 기준으로만 확장하는 것이 좋습니다.

## 왜 이제 제거했는가

이유는 3가지입니다.

1. 실사용 코드 참조가 사실상 새 구조로 모두 옮겨져 있었습니다.
2. 남아 있던 직접 참조는 스크립트 한 곳뿐이어서 안전하게 교체할 수 있었습니다.
3. 계속 유지하면 초보자 입장에서 읽기 경로가 두 갈래로 보이는 문제가 더 컸습니다.

## 지금의 기준

앞으로는 아래 기준만 유지하면 됩니다.

1. 실제 실행 로직은 `manufacturing_agent/`
2. Langflow 전용 로직은 `langflow_version/`
3. 문서와 테스트도 이 두 경로 기준으로 작성

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

## 초보자 관점에서의 권장 정책

초보자가 헷갈리지 않게 하려면 아래 원칙이 좋습니다.

1. 문서에서 `manufacturing_agent/` 가 실제 코드라고 계속 강조
2. Langflow 관련 설명은 `langflow_version/` 로만 연결
3. 새 예제, 새 테스트, 새 설명은 모두 새 구조 기준으로 작성

## 실무적으로 가장 안전한 운영안

지금 프로젝트에는 이 운영안이 가장 현실적입니다.

1. 새 개발은 `manufacturing_agent/` 와 `langflow_version/` 에만 진행
2. 문서와 테스트도 새 구조 기준으로만 확장
3. reference 성격의 오래된 문서는 점진적으로 새 경로 기준으로 갱신
4. 다시 호환 레이어를 만들 일은 실제 외부 의존이 확인될 때만 검토

## 같이 보면 좋은 문서

- [docs/START_HERE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/START_HERE.md)
- [docs/PYTHON_FILE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/PYTHON_FILE_GUIDE.md)
- [docs/FUNCTION_ROLE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/FUNCTION_ROLE_GUIDE.md)
