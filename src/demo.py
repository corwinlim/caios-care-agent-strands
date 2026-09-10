from .models import ActionClass, ActionProposal, Observation
from .policy import authorize_proposal, classify_observation

def scenario_a_governed_followup()->dict:
    obs=Observation("pika-demo","Eating normally; stool slightly soft; no vomiting.",["soft_stool"])
    proposal=ActionProposal("pika-demo","schedule_followup","Complete previously planned veterinary follow-up.",ActionClass.OWNER_APPROVAL)
    return {"scenario":"A","safety":classify_observation(obs).value,"before_approval":authorize_proposal(obs,proposal,owner_approved=False).value,"owner_approved":True,"after_approval":authorize_proposal(obs,proposal,owner_approved=True).value,"outcome":"Follow-up may proceed only after explicit owner approval."}

def scenario_b_red_flag_escalation()->dict:
    obs=Observation("pika-demo","Pet collapsed and has difficulty breathing.",["collapse","difficulty_breathing"])
    proposal=ActionProposal("pika-demo","schedule_followup","Ordinary follow-up",ActionClass.OWNER_APPROVAL)
    final_class=authorize_proposal(obs,proposal,owner_approved=True)
    return {"scenario":"B","safety":classify_observation(obs).value,"final_class":final_class.value,"ordinary_action_executed":False,"outcome":"Normal automation stops and professional escalation is surfaced."}

if __name__=='__main__':
    print(scenario_a_governed_followup())
    print(scenario_b_red_flag_escalation())
