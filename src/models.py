from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

class ActionClass(str, Enum):
    SAFE_AUTONOMOUS = "SAFE_AUTONOMOUS"
    OWNER_APPROVAL = "OWNER_APPROVAL"
    PROFESSIONAL_ESCALATION = "PROFESSIONAL_ESCALATION"

@dataclass(frozen=True)
class Observation:
    pet_id: str
    text: str
    tags: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class ActionProposal:
    pet_id: str
    action_type: str
    reason: str
    requested_class: ActionClass

@dataclass
class ActionOutcome:
    pet_id: str
    action_type: str
    action_class: ActionClass
    executed: bool
    authorized_by: Optional[str]
    record: str
