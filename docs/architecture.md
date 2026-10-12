# Agent Architecture

## High-level architecture

```mermaid
flowchart TD
    U[User Travel Request] --> L[LLM / Request Understanding]
    L --> M[Persistent Memory]
    M --> P[Planner]
    P --> F[Flight Search Tool]
    P --> H[Hotel Search Tool]
    P --> W[Weather Tool]

    F --> O[Observations]
    H --> O
    W --> O

    O --> R{Feasible Plan?}
    R -- No --> RP[Re-planning]
    RP --> F
    R -- Yes --> D[Reasoning + Final Plan]

    D --> A[Human Approval]
    A -- Reject --> S[Stop]
    A -- Approve --> B[Booking Action]
    B --> M
```

## Agent loop

```text
Observe → Plan → Act → Observe → Reason → Re-plan if required
```

The booking action is deliberately placed behind a human approval gate.
