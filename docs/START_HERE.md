# Start Here

가장 먼저 볼 파일은 `manufacturing_agent/agent.py` 입니다.

- `agent.py`
  - 외부에서 호출하는 진입점
- `graph/builder.py`
  - LangGraph 노드 연결
- `graph/nodes/`
  - 단계별 실행 단위
- `services/`
  - 실제 비즈니스 로직

코드를 읽을 때는 "질문 해석 -> retrieval 계획 -> retrieval 실행 -> 현재 데이터 분석 -> 응답 생성" 흐름으로 보면 가장 이해가 쉽습니다.
