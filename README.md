# CAIOS Care Agent — Strands

A clean-room public demonstration of a **governed veterinary follow-up agent** built with the Strands Agents SDK.

> Hackathon direction: reusable CAIOS capability + Amazon Build, Ship, Shape (Alexa+ / AWS Builder / Open Source).

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

## Architecture

Strands is the **orchestration adapter**. It can select and sequence bounded tools, but policy and authorization remain deterministic application authority.

## Tools

- `get_pet_context`
- `record_home_observation`
- `propose_followup_action`
- `request_owner_approval`
- `record_followup_outcome`
- `escalate_to_professional`

## Demo scenarios

### Scenario A — governed follow-up
A synthetic pet has a prior vet visit and a non-urgent owner update. The agent retrieves context, proposes a follow-up, requests owner approval, and records the outcome only after authorization.

### Scenario B — red-flag escalation
The owner reports collapse/difficulty breathing. Deterministic safety produces `PROFESSIONAL_ESCALATION`; normal follow-up is stopped.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q
python -m src.demo
```

To run the actual Strands agent, configure AWS credentials for a supported model provider and use:

```python
from src.agent import build_agent

agent = build_agent()
print(agent("Review Pika's home update and decide the safest next follow-up step."))
```

## IP boundary

This repository is intentionally clean-room. It does **not** contain CAIOS production source code, private datasets, production migrations, credentials, proprietary customer data, or private roadmap material.

## License

MIT.
