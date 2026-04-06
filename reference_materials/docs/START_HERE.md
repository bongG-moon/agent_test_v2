# 시작하기

이 문서는 LangGraph 버전을 처음 보는 사람이 가장 먼저 읽는 안내서입니다.  
목표는 "이 앱이 무엇을 하는지", "어떤 화면이 있는지", "LangGraph 버전이 왜 따로 있는지"를 빠르게 이해하는 것입니다.

## 1. 이 앱은 무엇을 하는가

이 앱은 제조 데이터를 자연어 질문으로 조회하는 도구입니다.  
단순 조회만 하는 것이 아니라, 필요하면 같은 턴에서 바로 후처리까지 수행합니다.

예:

1. `오늘 DA공정 생산량 알려줘`
2. `MODE별로 묶어줘`
3. `상위 5개만 보여줘`

1번은 조회, 2번과 3번은 후속 분석입니다.

또는 처음부터 이렇게 질문할 수도 있습니다.

```text
오늘 DA공정에서 MODE별 생산량 알려줘
```

이 경우 앱은:

- 생산 데이터를 조회하고
- MODE별 집계를 수행하고
- 최종 표를 바로 보여줍니다.

## 2. 화면은 두 개다

왼쪽 메뉴에서 아래 두 화면을 오갈 수 있습니다.

- `채팅 분석`
  - 실제 질문을 입력하는 화면입니다.
- `도메인 관리`
  - 사용자 도메인 지식을 등록하는 화면입니다.

## 3. 실행 방법

```bash
cd C:\Users\qkekt\Desktop\AGENT_COMPACT_LANGGRAPH
streamlit run app.py
```

## 4. 이 버전이 LangGraph인 이유

기본 버전은 함수가 순서대로 이어지는 구조입니다.  
LangGraph 버전은 그 흐름을 `StateGraph` 노드로 분리해 실행합니다.

현재 큰 흐름은 아래와 같습니다.

```text
run_agent()
  -> resolve_request
  -> plan_retrieval 또는 followup_analysis
  -> single_retrieval 또는 multi_retrieval
  -> finish
```

이 구조의 장점:

- 실행 단계를 더 명확하게 나눌 수 있습니다.
- 나중에 검증 노드, DB 전용 노드, 사람이 확인하는 노드 같은 확장이 쉬워집니다.
- 단계별 상태 추적이 더 자연스럽습니다.

## 5. 가장 먼저 해볼 질문

### 기본 조회

```text
오늘 DA공정 생산량 알려줘
```

### 복수 데이터셋 조회

```text
오늘 생산과 목표를 같이 보여줘
```

### 파생 지표 질문

```text
어제 DA공정에서 DDR5제품 생산 달성률 알려줘
```

이 질문은 LangGraph 내부에서 필요한 데이터셋 계획과 후처리를 연결하는지 보기 좋습니다.

## 6. 도메인 관리 화면에서는 무엇을 하나

사용자가 줄글로 아래 내용을 등록할 수 있습니다.

- 데이터셋 표현
  - 예: `양품률은 수율 데이터셋을 뜻해`
- 필터 별칭
  - 예: `후공정A는 D/A1, D/A2를 뜻해`
- 계산 규칙
  - 예: `홀드 부하지수는 hold_qty / production 으로 계산해줘`
- 판정 규칙
  - 예: `가동률이 85 미만이면 이상으로 판단해줘`

그리고 등록된 엔트리는 목록에서 확인하고 삭제할 수 있습니다.

## 7. 등록된 도메인은 어디에 저장되나

현재는 DB가 아니라 파일 기반입니다.

- 기본 도메인 지식
  - [`core/domain_knowledge.py`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/core/domain_knowledge.py)
- 사용자 등록 도메인
  - [`reference_materials/domain_registry/entries`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/domain_registry/entries)

즉, 사용자 등록 엔트리는 JSON 파일로 저장됩니다.

## 8. 다음으로 읽으면 좋은 문서

1. [`MANUFACTURING_AGENT_ROADMAP.md`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/docs/MANUFACTURING_AGENT_ROADMAP.md)
2. [`MANUFACTURING_AGENT_SLIDES.md`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/docs/MANUFACTURING_AGENT_SLIDES.md)
3. [`MANUFACTURING_AGENT_DIAGRAMS.md`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/docs/MANUFACTURING_AGENT_DIAGRAMS.md)
4. [`RUN_CHECKLIST.md`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/docs/RUN_CHECKLIST.md)
5. [`QUESTION_GUIDE.md`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/docs/QUESTION_GUIDE.md)
6. [`LANGGRAPH_DESIGN.md`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/docs/LANGGRAPH_DESIGN.md)
7. [`DOMAIN_GUIDE.md`](/Users/qkekt/Desktop/AGENT_COMPACT_LANGGRAPH/reference_materials/docs/DOMAIN_GUIDE.md)
