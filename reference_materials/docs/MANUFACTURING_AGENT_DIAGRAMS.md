# Manufacturing Agent Diagrams

이 문서는 제조 에이전트의 현재 구조와 앞으로 확장하려는 방향을 발표 자료나 설계 리뷰에서 바로 설명할 수 있도록 정리한 다이어그램 모음입니다.

## 1. 전체 발전 방향

```mermaid
flowchart LR
    P1["Phase 1<br/>Flexible Query & Analysis Foundation"] --> P2["Phase 2<br/>Reusable Pattern Library"]
    P2 --> P3["Phase 3<br/>End-to-End Process Agent"]
    P3 --> P4["Phase 4<br/>Experience & Recommendation Layer"]
    P4 --> P5["Phase 5<br/>Manufacturing Agent Platform"]
```

핵심 메시지:
- 현재 구현은 `Phase 1`에 해당합니다.
- 지금 구조는 이후 패턴형 업무 자동화와 공정별 에이전트 확장을 위한 기반입니다.

## 2. 현재 LangGraph 흐름

```mermaid
flowchart TD
    START([사용자 질문]) --> R1["resolve_request<br/>질문 해석 + 파라미터 추출"]
    R1 --> Q{"새 조회가 필요한가?"}

    Q -->|예| RP["plan_retrieval<br/>필요 데이터셋 결정"]
    Q -->|아니오| FA["followup_analysis<br/>현재 테이블 후처리"]

    RP --> M{"단일 조회인가?"}
    M -->|예| SR["single_retrieval"]
    M -->|아니오| MR["multi_retrieval"]

    SR --> S1{"후처리가 필요한가?"}
    S1 -->|예| PA1["analysis_after_retrieval"]
    S1 -->|아니오| FIN["finish"]
    PA1 --> FIN

    MR --> MB["analysis_base_table<br/>병합 기준 테이블 생성"]
    MB --> M2{"병합 후 분석 가능한가?"}
    M2 -->|예| PA2["analysis_after_multi_retrieval"]
    M2 -->|아니오| ERR1["병합 불가 안내"]
    PA2 --> FIN
    ERR1 --> FIN

    FA --> FIN
```

핵심 메시지:
- 먼저 `재조회`와 `현재 테이블 후처리`를 나눕니다.
- 재조회가 필요하면 다시 `단일`과 `다중` 흐름으로 분기합니다.
- 다중 조회는 바로 분석하지 않고 병합 안전성부터 확인합니다.

## 3. 현재 아키텍처 구성

```mermaid
flowchart LR
    U["사용자"] --> UI["UI / app.py"]
    UI --> ORCH["LangGraph Orchestrator"]

    ORCH --> PR["Parameter Service"]
    ORCH --> TP["Retrieval Planner"]
    ORCH --> DT["Data Retrieval"]
    ORCH --> MS["Merge Service"]
    ORCH --> AE["Analysis Engine"]
    ORCH --> RS["Response Service"]

    PR --> DK["Domain Knowledge"]
    TP --> DK
    AE --> DK
    MS --> DK
```

핵심 메시지:
- 그래프는 작게 유지하고, 실제 로직은 서비스 계층으로 분리했습니다.
- 도메인 지식은 파라미터 해석, 조회 계획, 병합, 분석에 공통으로 연결됩니다.

## 4. 도메인 규칙 반영 흐름

```mermaid
flowchart TD
    A["사용자 정의 규칙 등록"] --> B["dataset keywords"]
    A --> C["value groups"]
    A --> D["analysis rules"]
    A --> E["join rules"]

    B --> F["질문 해석 강화"]
    C --> G["필터 값 확장"]
    D --> H["필요 데이터셋 계획"]
    D --> I["계산 로직 보강"]
    E --> J["병합 규칙 보강"]

    F --> K["실행 흐름 반영"]
    G --> K
    H --> K
    I --> K
    J --> K
```

핵심 메시지:
- 등록된 규칙은 단순 메모가 아니라 실제 실행 흐름에 반영됩니다.
- 조회 계획과 분석 로직이 모두 도메인 규칙의 영향을 받습니다.

## 5. Langflow 전환 관점

```mermaid
flowchart LR
    A["LangGraph Node"] --> B["Service Function"]
    B --> C["Shared Core Logic"]
    C --> D["Langflow Component Wrapper"]
```

핵심 메시지:
- 핵심 로직을 서비스 함수로 분리했기 때문에 Langflow 컴포넌트로 감싸기 쉽습니다.
- 장기적으로는 `그래프 조립 방식만 다르고 코어 로직은 공유`하는 구조를 목표로 합니다.
