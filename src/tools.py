from dataclasses import asdict
from typing import Dict, List
try:
    from strands import tool
except Exception:
    def tool(func): return func
from .models import ActionClass, ActionOutcome, ActionProposal, Observation
from .policy import authorize_proposal, classify_observation
_CONTEXT={"pika-demo":{"pet_id":"pika-demo","name":"Pika","species":"dog","last_vet_visit":"2026-09-08","followup_due":True}}
_OUTCOMES: List[Dict]=[]

@tool
def get_pet_context(pet_id: str)->dict:
    """Return synthetic longitudinal context for a demo pet."""
    return _CONTEXT.get(pet_id,{"pet_id":pet_id,"status":"not_found"})

@tool
def record_home_observation(pet_id: str, text: str, tags: list[str])->dict:
    """Create a synthetic home observation. No diagnosis is produced."""
    obs=Observation(pet_id=pet_id,text=text,tags=tags)
    return {"observation":asdict(obs),"safety_class":classify_observation(obs).value}

@tool
def propose_followup_action(pet_id: str, action_type: str, reason: str, requested_class: str="OWNER_APPROVAL")->dict:
    """Create a bounded follow-up proposal. This does not authorize execution."""
    proposal=ActionProposal(pet_id=pet_id,action_type=action_type,reason=reason,requested_class=ActionClass(requested_class))
    return asdict(proposal)

@tool
def request_owner_approval(pet_id: str, action_type: str, reason: str, owner_approved: bool, observation_text: str, observation_tags: list[str])->dict:
    """Apply deterministic safety and explicit owner approval before consequential action."""
    obs=Observation(pet_id=pet_id,text=observation_text,tags=observation_tags)
    proposal=ActionProposal(pet_id=pet_id,action_type=action_type,reason=reason,requested_class=ActionClass.OWNER_APPROVAL)
    final_class=authorize_proposal(obs,proposal,owner_approved=owner_approved)
    if final_class is ActionClass.PROFESSIONAL_ESCALATION:
        return {"authorized":False,"action_class":final_class.value,"next_step":"escalate_to_professional"}
    if final_class is ActionClass.OWNER_APPROVAL and not owner_approved:
        return {"authorized":False,"action_class":final_class.value,"next_step":"await_owner_approval"}
    return {"authorized":True,"action_class":final_class.value,"next_step":"record_followup_outcome"}

@tool
def record_followup_outcome(pet_id: str, action_type: str, action_class: str, authorized_by: str, record: str)->dict:
    """Record the bounded outcome of an already authorized follow-up action."""
    outcome=ActionOutcome(pet_id=pet_id,action_type=action_type,action_class=ActionClass(action_class),executed=True,authorized_by=authorized_by,record=record)
    payload=asdict(outcome); _OUTCOMES.append(payload); return payload

@tool
def escalate_to_professional(pet_id: str, reason: str)->dict:
    """Stop normal automation and surface professional veterinary guidance."""
    return {"pet_id":pet_id,"action_class":ActionClass.PROFESSIONAL_ESCALATION.value,"executed":False,"message":"Normal automation stopped. Seek veterinary or emergency guidance.","reason":reason}
