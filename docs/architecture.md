# Architecture

```mermaid
flowchart LR
  A[Owner / Vet Input] --> B[Strands Agent Orchestration]
  B --> C[Deterministic Safety + Policy]
  C --> D{Authority Class}
  D -->|SAFE_AUTONOMOUS| E[Bounded Tool]
  D -->|OWNER_APPROVAL| F[Explicit Owner Approval]
  D -->|PROFESSIONAL_ESCALATION| G[Stop Automation + Escalate]
  F -->|approved| E
  E --> H[Outcome + Audit Record]
  I[Synthetic Longitudinal Pet Context] --> B
  C -. cannot be overridden by model .-> B
```

Authority path:

`observe -> classify -> propose -> authorize -> act -> record -> evaluate`

Strands owns orchestration, not safety authority. Deterministic application policy decides whether an action is safe, requires approval, or must stop and escalate.
