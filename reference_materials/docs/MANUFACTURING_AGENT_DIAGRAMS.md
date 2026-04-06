# Manufacturing Agent Diagrams

이 문서는 `PPT 장표에 바로 넣기 쉬운 실행 그래프` 중심으로 다시 정리한 문서입니다.

설계 문장보다 `노드`, `분기`, `합류`, `재시도`, `종료`가 한눈에 보이도록 구성했습니다.  
Mermaid를 그대로 붙여 넣거나, PNG/SVG로 변환해서 발표 자료에 넣는 용도로 사용할 수 있습니다.

## 1. 전체 Phase 로드맵 도식

```mermaid
flowchart LR
    P1["Phase 1<br/>Flexible Query & Analysis Foundation"] --> P2["Phase 2<br/>Reusable Process Pattern Library"]
    P2 --> P3["Phase 3<br/>End-to-End Process Agent"]
    P3 --> P4["Phase 4<br/>Experience & Recommendation Layer"]
    P4 --> P5["Phase 5<br/>Manufacturing Agent Platform"]

    P1A["자연어 질문 해석"]:::sub --> P1
    P1B["유연 조회 / 복수 조회"]:::sub --> P1
    P1C["pandas 후처리"]:::sub --> P1
    P1D["도메인 등록 / join 규칙 / 계산 규칙"]:::sub --> P1

    P2A["반복 업무 패턴 정리"]:::sub --> P2
    P2B["표준 데이터셋 조합"]:::sub --> P2
    P2C["패턴별 결과 포맷"]:::sub --> P2

    P3A["이상 탐지"]:::sub --> P3
    P3B["원인 후보별 추가 조회"]:::sub --> P3
    P3C["권장 조치 / Report"]:::sub --> P3

    P4A["사례 / 경험 데이터"]:::sub --> P4
    P4B["원인-조치 추천"]:::sub --> P4

    P5A["여러 제조 Agent 통합"]:::sub --> P5
    P5B["운영 / 권한 / 배치 / 배포"]:::sub --> P5

    classDef sub fill:#f7f7f7,stroke:#bbbbbb,color:#333333;
```

### 장표에서 강조할 메시지

- 현재는 `Phase 1`을 구현 중입니다.
- Phase 1은 나중의 프로세스 Agent를 가능하게 만드는 기반입니다.
- 이후 Phase는 지금 만든 기반 위에 쌓아 올리는 구조입니다.

## 2. 현재 Phase 1 전체 실행 그래프

```mermaid
flowchart TD
    START([사용자 질문]) --> R1["resolve_request<br/>질문 해석 + 파라미터 추출"]
    R1 --> Q{"현재 표로 충분한가?"}

    Q -->|아니오| RP["plan_retrieval<br/>필요 데이터셋 계획"]
    Q -->|예| FA["followup_analysis<br/>현재 표 후처리"]

    RP --> M{"복수 데이터셋이 필요한가?"}
    M -->|아니오| SR["single_retrieval"]
    M -->|예| MR["multi_retrieval"]

    SR --> S1{"후처리가 필요한가?"}
    S1 -->|아니오| FIN["finish"]
    S1 -->|예| PA1["analysis_after_retrieval"]
    PA1 --> FIN

    MR --> MB["analysis_base_table<br/>공통 기준 정리 + 병합"]
    MB --> M2{"분석 가능한가?"}
    M2 -->|예| PA2["analysis_after_multi_retrieval"]
    M2 -->|아니오| ERR1["공통 결합 기준 부족 안내"]
    PA2 --> FIN
    ERR1 --> FIN

    FA --> F1{"현재 표로 처리 가능한가?"}
    F1 -->|예| FIN
    F1 -->|아니오| RP

    FIN([최종 답변 + 표 표시])
```

### 장표에서 강조할 메시지

- 질문은 먼저 `새 조회`와 `기존 표 재사용`으로 갈립니다.
- 새 조회로 가면 다시 `단일 조회`와 `복수 조회`로 분기됩니다.
- 복수 조회는 바로 끝나지 않고 `병합 가능성 판단` 단계를 거칩니다.
- follow-up 분석도 필요하면 다시 retrieval로 되돌아갈 수 있습니다.

## 3. 현재 Phase 1 세부 실행 그래프

```mermaid
flowchart TD
    A["사용자 질문"] --> B["질문 해석"]
    B --> C["도메인 파라미터 추출"]
    C --> D["현재 데이터 메타데이터 확인"]
    D --> E{"새 조회 필요?"}

    E -->|예| F["retrieval planning"]
    E -->|아니오| G["follow-up transform"]

    F --> H["dataset 후보 선정"]
    H --> I["analysis rule / join rule 보강"]
    I --> J{"single or multi?"}

    J -->|single| K["원천 데이터 조회"]
    J -->|multi| L["여러 데이터셋 조회"]

    K --> M{"post-processing 필요?"}
    M -->|예| N["pandas code generation"]
    M -->|아니오| R["response generation"]

    L --> O["join key 후보 선정"]
    O --> P["join type 결정"]
    P --> Q["cardinality 점검"]
    Q --> Q2{"many-to-many 인가?"}
    Q2 -->|예| Q3["key refinement 시도"]
    Q2 -->|아니오| N
    Q3 --> Q4{"refinement 성공?"}
    Q4 -->|예| N
    Q4 -->|아니오| S["안전한 병합 중단 / 에러 안내"]

    G --> N
    N --> T{"분석 성공?"}
    T -->|예| R
    T -->|아니오| U["retry or minimal fallback"]
    U --> R

    S --> R
    R --> V([최종 답변])
```

### 장표에서 강조할 메시지

- 이 그림은 “실제 내부에서 어떤 판단이 이어지는지”를 보여주는 운영용 그래프입니다.
- 단순 LLM 답변이 아니라 `계획 -> 조회 -> 병합 -> 분석 -> 응답`이 단계적으로 이어집니다.

## 4. 현재 시스템 아키텍처 그래프

```mermaid
flowchart LR
    U["사용자"] --> UI["Streamlit UI"]
    UI --> ORCH["LangGraph Orchestrator"]

    ORCH --> PR["Parameter Resolver"]
    ORCH --> TP["Retrieval Planner"]
    ORCH --> DT["Data Tools"]
    ORCH --> AE["Analysis Engine"]
    ORCH --> RG["Response Generator"]

    PR --> DK["Domain Knowledge"]
    TP --> DK
    AE --> DK

    DK --> BK["기본 도메인 지식"]
    DK --> CK["사용자 등록 도메인"]

    DT --> D1["생산"]
    DT --> D2["목표"]
    DT --> D3["재공"]
    DT --> D4["설비"]
    DT --> D5["수율"]
    DT --> D6["홀드 / 스크랩 / LOT"]

    AE --> PD["pandas 처리"]
    RG --> OUT["답변 + 표 + 요약"]
```

### 장표에서 강조할 메시지

- UI, Orchestrator, Domain, Retrieval, Analysis가 분리되어 있습니다.
- 사용자 도메인 등록은 단순 메모가 아니라 Planner와 Analysis에 직접 연결됩니다.

## 5. 도메인 지식 반영 그래프

```mermaid
flowchart TD
    A["사용자 줄글 입력"] --> B["도메인 관리 UI"]
    B --> C["구조화 변환"]

    C --> D["dataset keywords"]
    C --> E["value groups"]
    C --> F["analysis rules"]
    C --> G["join rules"]

    D --> H["질문 해석 강화"]
    E --> I["필터 확장"]
    F --> J["필요 데이터셋 계획 강화"]
    F --> K["pandas 계산 로직 강화"]
    G --> L["복수 테이블 결합 규칙 강화"]

    H --> M["실행 흐름 반영"]
    I --> M
    J --> M
    K --> M
    L --> M
```

### 장표에서 강조할 메시지

- 도메인 등록은 별도 저장만 하는 기능이 아닙니다.
- 질문 해석, 데이터 계획, 후처리, join 전략까지 실제 실행에 반영됩니다.

## 6. Phase 2 패턴 Agent 실행 그래프

```mermaid
flowchart TD
    A([사용자 질문]) --> B["패턴 분류"]
    B --> C{"등록된 반복 패턴인가?"}

    C -->|예| D["Pattern Agent 선택"]
    C -->|아니오| E["Phase 1 유연 분석 엔진"]

    D --> F["표준 데이터셋 조합 실행"]
    F --> G["표준 계산 로직 실행"]
    G --> H["패턴별 결과 포맷"]
    H --> I([최종 답변])

    E --> I
```

### 장표에서 강조할 메시지

- Phase 2는 Phase 1을 버리는 것이 아니라, 그 위에 `패턴용 빠른 경로`를 추가하는 구조입니다.
- 반복 업무일수록 더 안정적이고 예측 가능한 실행이 가능해집니다.

## 7. Phase 3 프로세스 Agent 실행 그래프

```mermaid
flowchart TD
    A([프로세스 Agent 요청]) --> B["업무 목적 해석"]
    B --> C["핵심 KPI/이상 조건 확인"]
    C --> D["1차 이상 탐지"]
    D --> E{"이상 존재?"}

    E -->|아니오| F["정상 요약 Report"]
    E -->|예| G["원인 후보 트리 생성"]

    G --> H["재공 데이터 조회"]
    G --> I["설비 데이터 조회"]
    G --> J["수율 / 홀드 데이터 조회"]

    H --> K["원인 후보 통합 평가"]
    I --> K
    J --> K

    K --> L["세부 drill-down 분석"]
    L --> M["권장 조치 추천"]
    M --> N["Report 생성"]
    F --> O([최종 결과])
    N --> O
```

### 장표에서 강조할 메시지

- 이 단계부터는 단순 조회가 아니라 업무 프로세스를 한 번에 수행합니다.
- 여러 하위 분석이 병렬 또는 순차로 연결되는 구조를 가집니다.

## 8. 생산 이상 분석 프로세스 Agent 상세 그래프

```mermaid
flowchart TD
    A([생산 이상 분석 요청]) --> B["생산 데이터 조회"]
    A --> C["목표 데이터 조회"]

    B --> D["제품별 생산 실적 계산"]
    C --> E["제품별 목표 대비 비교"]
    D --> E

    E --> F{"생산 저조 제품 존재?"}
    F -->|아니오| G["정상 요약 생성"]
    F -->|예| H["문제 제품 목록 추출"]

    H --> I["재공 원인 확인"]
    H --> J["설비 원인 확인"]
    H --> K["수율 / 홀드 원인 확인"]

    I --> L["원인별 스코어링"]
    J --> L
    K --> L

    L --> M["세부 drill-down"]
    M --> N["조치 추천"]
    N --> O["최종 Report"]
    G --> P([결과 제공])
    O --> P
```

### 장표에서 강조할 메시지

- 이 그림은 `앞으로 구현하려는 End-to-End Agent`의 대표 예시입니다.
- 단순히 “생산이 낮다”를 보여주는 것이 아니라, 원인과 조치까지 연결합니다.

## 9. 장기 확장 그래프

```mermaid
flowchart LR
    A["분석 결과"] --> B["사례 / 경험 데이터 연결"]
    B --> C["원인-조치 추천"]
    C --> D["사용자 조치 실행"]
    D --> E["조치 결과 축적"]
    E --> F["운영 지식 업데이트"]
    F --> G["다음 분석 품질 향상"]
```

### 장표에서 강조할 메시지

- 최종 목표는 “한 번 답하고 끝나는 분석기”가 아니라,
- 조직의 경험을 축적하면서 더 좋아지는 제조 Agent 플랫폼입니다.
