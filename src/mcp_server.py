from __future__ import annotations

from typing import Any

REQUIRED_TOOL_NAMES = {
    "get_pet_context",
    "record_home_observation",
    "propose_followup_action",
    "request_owner_approval",
    "record_followup_outcome",
    "escalate_to_professional",
}

try:
    from mcp.server import MCPServer
except ImportError:
    MCPServer = None


class DependencyUnavailableApp:
    """Fail-closed ASGI app used only when the official MCP SDK is absent."""

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            return
        body = b'{"error":"mcp_sdk_unavailable"}'
        await send({
            "type": "http.response.start",
            "status": 503,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({"type": "http.response.body", "body": body})


def build_mcp_server():
    if MCPServer is None:
        raise RuntimeError("MCP SDK unavailable. Install project dependencies first.")

    from .authorization import AuthorizationStore
    from .models import ActionClass, ActionProposal, Observation
    from .policy import authorize_proposal, classify_observation

    authorization_store = AuthorizationStore()
    server = MCPServer("CAIOS Care Agent")

    @server.tool()
    def get_pet_context(pet_id: str) -> dict:
        """Return bounded synthetic longitudinal context for a demo pet."""
        if pet_id != "pika-demo":
            return {"pet_id": pet_id, "status": "not_found"}
        return {
            "pet_id": "pika-demo",
            "name": "Pika",
            "species": "dog",
            "last_vet_visit": "2026-09-08",
            "followup_due": True,
        }

    @server.tool()
    def record_home_observation(pet_id: str, text: str, tags: list[str]) -> dict:
        """Record a synthetic home observation without diagnosis."""
        obs = Observation(pet_id=pet_id, text=text, tags=tags)
        return {"pet_id": pet_id, "safety_class": classify_observation(obs).value}

    @server.tool()
    def propose_followup_action(pet_id: str, action_type: str, reason: str) -> dict:
        """Create a bounded proposal; this does not authorize execution."""
        return {
            "pet_id": pet_id,
            "action_type": action_type,
            "reason": reason,
            "requested_class": ActionClass.OWNER_APPROVAL.value,
        }

    @server.tool()
    def request_owner_approval(
        pet_id: str,
        action_type: str,
        reason: str,
        owner_approved: bool,
        observation_text: str,
        observation_tags: list[str],
    ) -> dict:
        """Apply deterministic safety and explicit owner approval."""
        observation = Observation(pet_id=pet_id, text=observation_text, tags=observation_tags)
        proposal = ActionProposal(
            pet_id=pet_id,
            action_type=action_type,
            reason=reason,
            requested_class=ActionClass.OWNER_APPROVAL,
        )
        final_class = authorize_proposal(observation, proposal, owner_approved=owner_approved)

        if final_class is ActionClass.PROFESSIONAL_ESCALATION:
            return {
                "authorized": False,
                "action_class": final_class.value,
                "next_step": "escalate_to_professional",
            }
        if final_class is ActionClass.OWNER_APPROVAL and not owner_approved:
            return {
                "authorized": False,
                "action_class": final_class.value,
                "next_step": "await_owner_approval",
            }

        receipt = authorization_store.issue(
            pet_id=pet_id,
            action_type=action_type,
            authorized_by="owner" if owner_approved else "policy",
        )
        return {
            "authorized": True,
            "action_class": final_class.value,
            "authorization_id": receipt.authorization_id,
            "next_step": "record_followup_outcome",
        }

    @server.tool()
    def record_followup_outcome(
        pet_id: str,
        action_type: str,
        authorization_id: str,
        record: str,
    ) -> dict:
        """Record an outcome only after consuming a matching one-time authorization receipt."""
        receipt = authorization_store.consume(
            authorization_id,
            pet_id=pet_id,
            action_type=action_type,
        )
        return {
            "pet_id": pet_id,
            "action_type": action_type,
            "authorized_by": receipt.authorized_by,
            "record": record,
            "executed": True,
        }

    @server.tool()
    def escalate_to_professional(pet_id: str, reason: str) -> dict:
        """Stop normal automation and surface professional veterinary guidance."""
        return {
            "pet_id": pet_id,
            "action_class": ActionClass.PROFESSIONAL_ESCALATION.value,
            "executed": False,
            "reason": reason,
        }

    return server


if MCPServer is None:
    app = DependencyUnavailableApp()
else:
    app = build_mcp_server().streamable_http_app()
