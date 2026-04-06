# Migration To Langflow

Langflow 전환 시 유지하면 좋은 규칙:

- 서비스 함수는 `dict -> dict` 형태 유지
- 노드 wrapper는 얇게 유지
- 도메인 지식과 데이터 로직은 LangGraph/Langflow 밖의 공통 모듈로 유지
- DataFrame 대신 `list[dict]` 결과를 기본 계약으로 사용

추천 매핑:

- `extract_params_component` -> 파라미터 추출 노드
- `decide_query_mode_component` -> 분기 판단 노드
- `plan_retrieval_component` -> planner 노드
- `retrieval_component` -> retriever 노드
- `followup_analysis_component` -> analysis 노드

즉, LangGraph와 Langflow는 오케스트레이션 레이어만 달라지고, 코어 서비스는 공유하는 구조를 목표로 합니다.
