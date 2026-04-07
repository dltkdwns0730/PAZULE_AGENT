# 파이프라인 시각화

> **분류**: 레퍼런스 · **버전**: v2.3 · **최종 수정**: 2026-04-07
>
> `POST /api/mission/submit` 요청 시 실행되는 LangGraph 파이프라인의 Mermaid 다이어그램.

---

## 전체 파이프라인

```mermaid
graph TD
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px
    classDef startEnd fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724
    classDef decision fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#856404
    classDef model fill:#cce5ff,stroke:#007bff,stroke-width:2px,color:#004085
    classDef fail fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#721c24
    classDef proxy fill:#e2e3e5,stroke:#6c757d,stroke-width:2px,color:#383d41

    START((START)):::startEnd
    END_NODE((END)):::startEnd

    validator[validator]:::decision
    router[router]:::proxy

    evaluator[evaluator]:::model

    subgraph Models
        siglip2(SigLIP2)
        blip(BLIP)
        qwen(Qwen VL)
    end
    evaluator -.-> siglip2
    evaluator -.-> blip
    evaluator -.-> qwen

    aggregator[aggregator]:::proxy
    council[council]:::model
    judge[judge]:::decision

    policy[policy]:::decision

    responder_success[responder — Success]:::startEnd
    responder_fail[responder — Fail]:::fail
    responder_error[responder — Error]:::fail

    START --> validator

    validator -- Pass --> router
    validator -- Fail --> responder_error

    router --> evaluator

    siglip2 -.-> aggregator
    blip -.-> aggregator
    qwen -.-> aggregator

    aggregator --> council
    council --> judge

    judge -- Success --> policy
    judge -- Fail --> responder_fail

    policy --> responder_success

    responder_success --> END_NODE
    responder_fail --> END_NODE
    responder_error --> END_NODE
```

---

## 참고

- 실선: 순차 실행 흐름
- 점선: 모델 fan-out / fan-in
- 조건 분기: validator 후 (gate 통과 여부), judge 후 (판정 성공 여부)
- 상세 설계: [`architecture.md`](./architecture.md)
