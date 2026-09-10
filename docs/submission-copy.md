# Submission Copy

## Project
CAIOS Care Agent

## Positioning
A governed Strands agent for safer veterinary follow-up, with deterministic red flags, explicit approval gates, and auditable outcomes.

## Short pitch
CAIOS Care Agent helps veterinary professionals and pet owners turn fragmented follow-up context into a governed workflow. Strands Agents orchestrates bounded tools, while deterministic policy decides whether an action is safe to automate, requires owner approval, or must escalate to a veterinary professional.

## What it does
The agent retrieves synthetic longitudinal pet context, records home observations, proposes follow-up actions, requests explicit owner approval for consequential steps, records outcomes, and stops ordinary automation when deterministic red flags are detected.

## Why Strands
Strands Agents is used as the orchestration layer for tool selection and sequencing. Domain authority stays outside the model: red-flag safety and action authorization are deterministic and cannot be overridden by the LLM.

## Demo proof points
1. Non-urgent update → OWNER_APPROVAL → no execution before approval → outcome recorded after approval.
2. Red-flag update → PROFESSIONAL_ESCALATION → normal automation blocked.
