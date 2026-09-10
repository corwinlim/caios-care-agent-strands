from strands import Agent
from .tools import escalate_to_professional,get_pet_context,propose_followup_action,record_followup_outcome,record_home_observation,request_owner_approval
SYSTEM_PROMPT="""You are CAIOS Care Agent, a veterinary follow-up workflow assistant.
Hard rules:
1. Never diagnose.
2. Never recommend or change medication or treatment.
3. Red-flag safety always overrides ordinary workflow.
4. Consequential follow-up actions require explicit owner approval.
5. If a tool reports PROFESSIONAL_ESCALATION, stop normal automation.
6. Use only supplied synthetic demo context.
7. Record an outcome only after policy reports authorized=true.
"""
def build_agent()->Agent:
    return Agent(system_prompt=SYSTEM_PROMPT,tools=[get_pet_context,record_home_observation,propose_followup_action,request_owner_approval,record_followup_outcome,escalate_to_professional])
