from .models import ActionClass, ActionProposal, Observation

RED_FLAG_TAGS={"collapse","difficulty_breathing","seizure","uncontrolled_bleeding"}
SAFE_ACTION_TYPES={"collect_context","send_reminder"}
OWNER_APPROVAL_ACTION_TYPES={"schedule_followup","share_vet_summary"}

def classify_observation(observation: Observation)->ActionClass:
    if RED_FLAG_TAGS.intersection(set(observation.tags)):
        return ActionClass.PROFESSIONAL_ESCALATION
    return ActionClass.OWNER_APPROVAL

def authorize_proposal(observation: Observation, proposal: ActionProposal, *, owner_approved: bool=False)->ActionClass:
    safety=classify_observation(observation)
    if safety is ActionClass.PROFESSIONAL_ESCALATION:
        return safety
    if proposal.action_type in SAFE_ACTION_TYPES:
        return ActionClass.SAFE_AUTONOMOUS
    if proposal.action_type in OWNER_APPROVAL_ACTION_TYPES:
        return ActionClass.OWNER_APPROVAL
    return ActionClass.PROFESSIONAL_ESCALATION
