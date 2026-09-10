from src.models import ActionClass, ActionProposal, Observation
from src.policy import authorize_proposal, classify_observation

def test_owner_approval_required_for_followup():
    obs=Observation("pika-demo","stable",["soft_stool"])
    proposal=ActionProposal("pika-demo","schedule_followup","routine",ActionClass.OWNER_APPROVAL)
    assert authorize_proposal(obs,proposal,owner_approved=False)==ActionClass.OWNER_APPROVAL

def test_red_flag_escalation_overrides_owner_approval():
    obs=Observation("pika-demo","collapsed",["collapse"])
    proposal=ActionProposal("pika-demo","schedule_followup","routine",ActionClass.OWNER_APPROVAL)
    assert classify_observation(obs)==ActionClass.PROFESSIONAL_ESCALATION
    assert authorize_proposal(obs,proposal,owner_approved=True)==ActionClass.PROFESSIONAL_ESCALATION

def test_unknown_consequential_action_fails_closed():
    obs=Observation("pika-demo","stable",[])
    proposal=ActionProposal("pika-demo","change_medication","unsafe",ActionClass.OWNER_APPROVAL)
    assert authorize_proposal(obs,proposal,owner_approved=True)==ActionClass.PROFESSIONAL_ESCALATION
