import pytest
from src.authorization import AuthorizationStore


def test_issue_and_consume_matching_receipt_once():
    store = AuthorizationStore()
    receipt = store.issue(pet_id="pika-demo", action_type="schedule_followup", authorized_by="owner")
    consumed = store.consume(receipt.authorization_id, pet_id="pika-demo", action_type="schedule_followup")
    assert consumed.authorized_by == "owner"
    with pytest.raises(ValueError, match="authorization receipt invalid or already used"):
        store.consume(receipt.authorization_id, pet_id="pika-demo", action_type="schedule_followup")


def test_receipt_rejects_cross_pet_or_cross_action_use():
    store = AuthorizationStore()
    receipt = store.issue(pet_id="pika-demo", action_type="schedule_followup", authorized_by="owner")
    with pytest.raises(ValueError, match="authorization receipt mismatch"):
        store.consume(receipt.authorization_id, pet_id="other-pet", action_type="schedule_followup")


def test_unknown_receipt_fails_closed():
    store = AuthorizationStore()
    with pytest.raises(ValueError, match="authorization receipt invalid or already used"):
        store.consume("missing", pet_id="pika-demo", action_type="schedule_followup")
