# CAIOS Care Agent — Strands + MCP

A clean-room demonstration of a **governed veterinary follow-up agent** using the Strands Agents SDK and a self-hosted Model Context Protocol surface for Alexa+ / Amazon Build, Ship, Shape.

> Hackathon direction: Alexa+ primary track + AWS Builder + Open Source mini challenges.

## Problem

Longitudinal pet context is fragmented between owner messages, prior visits, reminders, and follow-up actions. Veterinary teams spend time reconstructing what happened at home before they can decide what needs attention.

CAIOS Care Agent demonstrates a safer workflow:

`observe -> classify -> propose -> authorize -> act -> record -> evaluate`

The agent helps compress home-to-clinic follow-up work **without becoming an autonomous diagnostic or treatment system**.

## Safety model

Three action classes are enforced by deterministic policy:

- `SAFE_AUTONOMOUS`: low-risk context collection or reminders only.
- `OWNER_APPROVAL`: consequential follow-up actions require explicit owner confirmation.
- `PROFESSIONAL_ESCALATION`: red flags stop ordinary automation and surface veterinary/emergency guidance.

Hard rules:
- no autonomous diagnosis;
- no medication or treatment changes;
- deterministic red flags run before normal agent continuation;
- professional escalation cannot be overridden by the model;
- every executed action is auditable;
- synthetic demo data only.

## Alexa+ MCP surface

The repository exposes the governed workflow as a self-hosted MCP server over **Streamable HTTP** using the official Python SDK. The current SDK serves the 2025-11-25 protocol era required by the Amazon hackathon and later protocol revisions from the same server.

The endpoint is:

`POST /mcp`

Start it with:

```bash
uvicorn src.mcp_server:app --host 0.0.0.0 --port 8000
```

If the MCP SDK is missing, the application fails closed with HTTP 503 instead of silently substituting a fake protocol implementation.

## Architecture

Strands is the **agent orchestration adapter**. MCP is the **external agent/tool transport**. Neither is the final authority for consequential actions: deterministic CAIOS policy performs safety classification and authorization.

## Governed MCP tools

- `get_pet_context`
- `record_home_observation`
- `propose_followup_action`
- `request_owner_approval`
- `record_followup_outcome`
- `escalate_to_professional`

## Demo scenarios

### Scenario A — governed follow-up

A synthetic pet has a prior vet visit and a non-urgent owner update. The system retrieves context, proposes a follow-up, requires owner approval, and records the outcome only after authorization.

### Scenario B — red-flag escalation

The owner reports collapse or difficulty breathing. Deterministic safety produces `PROFESSIONAL_ESCALATION`; normal follow-up is stopped even if an owner previously approved an ordinary action.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q
python -m src.demo
uvicorn src.mcp_server:app --host 127.0.0.1 --port 8000
```

To run the model-backed Strands agent, configure AWS credentials for a supported model provider and use:

```python
from src.agent import build_agent

agent = build_agent()
print(agent("Review Pika's home update and decide the safest next follow-up step."))
```

## Verification status

Verified locally:
- deterministic action policy;
- owner approval gating;
- red-flag escalation override;
- fail-closed unknown consequential action;
- MCP module contract and ASGI export.

Not yet claimed as verified:
- live MCP client/server handshake in this execution environment;
- model-backed Strands call against AWS;
- deployed public endpoint.

## IP boundary

This repository is intentionally clean-room. It does **not** contain CAIOS production source code, private datasets, production migrations, credentials, proprietary customer data, or private roadmap material.

## License

MIT.
