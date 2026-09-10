# CAIOS Care Agent — Demo Script

## Problem
Veterinary follow-up is often fragmented across owner messages, prior visits, reminders, and home observations. The cost is not just time: important context can be missed, while unsafe automation is unacceptable.

## Product
CAIOS Care Agent is a governed veterinary follow-up agent. It uses Strands Agents for orchestration, while deterministic policy controls authority. The workflow is: observe → classify → propose → authorize → act → record → evaluate.

## Scenario A: governed follow-up
1. Show synthetic pet context for Pika.
2. Enter a non-urgent update: “Eating normally. Stool slightly soft today. No vomiting.”
3. Show the agent retrieving context and proposing a follow-up action.
4. Show `OWNER_APPROVAL` classification.
5. Demonstrate that the action cannot execute before approval.
6. Approve explicitly.
7. Show the outcome record containing reason, authorization, and result.

Narration: “Strands decides which bounded tool to call, but it does not own authorization. The deterministic policy layer does.”

## Scenario B: red-flag escalation
1. Enter: “Pet collapsed and has difficulty breathing.”
2. Show deterministic red-flag classification.
3. Show `PROFESSIONAL_ESCALATION`.
4. Show that ordinary follow-up execution is blocked.

Narration: “The model cannot override this branch. Normal automation stops and the system surfaces veterinary or emergency guidance.”

## Architecture
- Strands Agent = orchestration adapter.
- Deterministic safety + policy = authority.
- Bounded tools = controlled capabilities.
- Synthetic longitudinal context = demo data.
- Outcome + audit record = accountability.

## Why it matters
For veterinary professionals, the goal is fewer minutes spent reconstructing follow-up context, better completeness of home-to-clinic information, and more reliable owner follow-through—without turning the agent into an autonomous diagnostic or treatment system.
