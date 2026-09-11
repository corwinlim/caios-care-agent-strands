from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from .alexa_auth import AlexaServiceAuthApp
from .protocol_selftest import run_protocol_selftest
from .readiness import readiness_snapshot

REQUIRED_TOOL_NAMES = {
    "get_pet_context",
    "record_home_observation",
    "propose_followup_action",
    "request_owner_approval",
    "record_followup_outcome",
    "escalate_to_professional",
}

_background_tasks: set[asyncio.Task] = set()

try:
    from mcp.server import MCPServer
except ImportError:
    MCPServer = None


class DependencyUnavailableApp:
    """Fail-closed ASGI app used only when the official MCP SDK is absent."""

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        if scope.get("type") != "http":
            return
        await _send_json(send, 503, {"error": "mcp_sdk_unavailable"})


async def _send_json(send: Any, status: int, payload: dict) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
    })
    await send({"type": "http.response.body", "body": body})


async def _log_protocol_selftest() -> None:
    try:
        snapshot = await run_protocol_selftest(int(os.environ.get("PORT", "10000")))
        print("CAIOS_MCP_PROTOCOL_SELFTEST " + json.dumps(snapshot, sort_keys=True), flush=True)
    except Exception as exc:
        print(
            "CAIOS_MCP_PROTOCOL_SELFTEST "
            + json.dumps({"ok": False, "error_type": type(exc).__name__, "error": str(exc)[:300]}, sort_keys=True),
            flush=True,
        )


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
        try:
            receipt = authorization_store.consume(
                authorization_id,
                pet_id=pet_id,
                action_type=action_type,
            )
        except ValueError as exc:
            reason = str(exc)
            error = (
                "authorization_receipt_mismatch"
                if "mismatch" in reason
                else "authorization_receipt_invalid_or_used"
            )
            return {
                "pet_id": pet_id,
                "action_type": action_type,
                "executed": False,
                "error": error,
            }
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


mcp_server = build_mcp_server() if MCPServer is not None else None
mcp_app = mcp_server.streamable_http_app() if mcp_server is not None else DependencyUnavailableApp()


class ServiceApp:
    """Small ASGI wrapper that exposes health/readiness while preserving MCP lifespan and routing."""

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") == "lifespan":
            async def send_with_readiness(message: dict) -> None:
                await send(message)
                if message.get("type") == "lifespan.startup.complete" and mcp_server is not None:
                    snapshot = await readiness_snapshot(mcp_server, REQUIRED_TOOL_NAMES)
                    print("CAIOS_MCP_READINESS " + json.dumps(snapshot, sort_keys=True), flush=True)
                    task = asyncio.create_task(_log_protocol_selftest())
                    _background_tasks.add(task)
                    task.add_done_callback(_background_tasks.discard)

            await mcp_app(scope, receive, send_with_readiness)
            return

        if scope.get("type") != "http":
            await mcp_app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path == "/health":
            await _send_json(send, 200, {
                "status": "ok",
                "service": "caios-care-agent-strands",
                "transport": "streamable-http",
            })
            return

        if path == "/ready":
            if mcp_server is None:
                await _send_json(send, 503, {
                    "ready": False,
                    "registered_tools": [],
                    "missing_tools": sorted(REQUIRED_TOOL_NAMES),
                    "reason": "mcp_sdk_unavailable",
                })
                return
            snapshot = await readiness_snapshot(mcp_server, REQUIRED_TOOL_NAMES)
            await _send_json(send, 200 if snapshot["ready"] else 503, snapshot)
            return

        await mcp_app(scope, receive, send)


app = AlexaServiceAuthApp(ServiceApp())
