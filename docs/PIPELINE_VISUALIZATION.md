# PAZULE Pipeline Architecture

This document contains the Mermaid diagram for the updated PAZULE execution pipeline, utilizing domain-driven node names (`validator`, `router`, `evaluator`, etc.) and the latest model strategy (SigLIP2, Qwen, BLIP).

You can render this diagram using Markdown viewers that support Mermaid (like GitHub, GitLab, or VS Code extensions).

```mermaid
graph TD
    %% Define Styles
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef startEnd fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724;
    classDef decision fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#856404;
    classDef model fill:#cce5ff,stroke:#007bff,stroke-width:2px,color:#004085;
    classDef fail fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#721c24;
    classDef proxy fill:#e2e3e5,stroke:#6c757d,stroke-width:2px,color:#383d41;

    %% Nodes
    START((START)):::startEnd
    END_NODE((END)):::startEnd

    validator[validator<br/>(Gate Keeper)]:::decision
    router[router<br/>(Task Router)]:::proxy
    
    evaluator[evaluator<br/>(Model Fanout)]:::model
    
    %% Models
    subgraph Models
        siglip2(SigLIP2)
        blip(BLIP)
        qwen(Qwen-VL)
    end
    evaluator -.-> siglip2
    evaluator -.-> blip
    evaluator -.-> qwen
    
    aggregator[aggregator<br/>(Evidence Aggregator)]:::proxy
    council[council<br/>(Deliberation)]:::model
    judge[judge<br/>(Decision Engine)]:::decision
    
    policy[policy<br/>(Coupon Engine)]:::decision
    
    responder_success[responder<br/>(Success)]:::startEnd
    responder_fail[responder<br/>(Fail)]:::fail
    responder_error[responder<br/>(Error)]:::fail

    %% Flow
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
