# Node Guide

권장 원칙:

- 노드 하나는 한 가지 일만 한다.
- 노드는 가능한 한 `state in -> state delta out` 형태를 유지한다.
- 복잡한 로직은 서비스 함수로 이동한다.
- Streamlit 세션 상태를 노드에서 직접 만지지 않는다.

현재 노드:

- `resolve_request_node`
- `plan_retrieval_node`
- `single_retrieval_node`
- `multi_retrieval_node`
- `followup_analysis_node`
- `finish_node`

Langflow로 옮길 때도 같은 경계를 유지하는 것이 좋습니다.
