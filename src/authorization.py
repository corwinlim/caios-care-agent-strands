from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class AuthorizationReceipt:
    authorization_id: str
    pet_id: str
    action_type: str
    authorized_by: str


class AuthorizationStore:
    def __init__(self) -> None:
        self._active: dict[str, AuthorizationReceipt] = {}

    def issue(self, *, pet_id: str, action_type: str, authorized_by: str) -> AuthorizationReceipt:
        receipt = AuthorizationReceipt(
            authorization_id=str(uuid4()),
            pet_id=pet_id,
            action_type=action_type,
            authorized_by=authorized_by,
        )
        self._active[receipt.authorization_id] = receipt
        return receipt

    def consume(self, authorization_id: str, *, pet_id: str, action_type: str) -> AuthorizationReceipt:
        receipt = self._active.get(authorization_id)
        if receipt is None:
            raise ValueError("authorization receipt invalid or already used")
        if receipt.pet_id != pet_id or receipt.action_type != action_type:
            raise ValueError("authorization receipt mismatch")
        del self._active[authorization_id]
        return receipt
