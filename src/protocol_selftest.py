from __future__ import annotations

import asyncio
import base64
import json
import os
from typing import Any

import httpx

from .protocol_helpers import tool_call_failed_closed, tool_result_payload

PROTOCOL_VERSION = "2025-11-25"


def extract_jsonrpc_payload(content_type: str, body: str) -> dict:
    if "text/event-stream" not in content_type:
        return json.loads(body)

    for line in body.splitlines():
        if line.startswith("data:"):
            return json.loads(line.split(":", 1)[1].strip())
    raise ValueError("no JSON-RPC data event found")


async def _service_token(client: httpx.AsyncClient, port: int) -> str | None:
    client_id = os.environ.get("ALEXA_MCP_CLIENT_ID", "")
    client_secret = os.environ.get("ALEXA_MCP_CLIENT_SECRET", "")
    base_url = os.environ.get("ALEXA_MCP_BASE_URL", "").rstrip("/")
    if not (client_id and client_secret and base_url):
        return None

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = await client.post(
        f"http://127.0.0.1:{port}/oauth/token",
        headers={
            "authorization": f"Basic {basic}",
            "content-type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "scope": "mcp:service",
            "resource": f"{base_url}/mcp",
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


async def _call_tool(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    request_id: int,
    name: str,
    arguments: dict[str, Any],
) -> dict:
    response = await client.post(
        url,
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
    )
    response.raise_for_status()
    return extract_jsonrpc_payload(response.headers.get("content-type", ""), response.text)


async def run_protocol_selftest(port: int) -> dict[str, Any]:
    """Exercise the deployed MCP wire path over localhost HTTP.

    Covers service authentication when configured, protocol negotiation, tool
    discovery, a safe read-only tool call, owner-approval receipt
    issuance/consumption/replay rejection, and red-flag escalation that cannot
    be overridden by owner approval.
    """
    await asyncio.sleep(0.75)
    url = f"http://127.0.0.1:{port}/mcp"

    async with httpx.AsyncClient(timeout=10.0) as client:
        service_token = await _service_token(client, port)
        base_headers = {
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
        }
        if service_token:
            base_headers["authorization"] = f"Bearer {service_token}"

        init_response = await client.post(
            url,
            headers=base_headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "caios-runtime-selftest", "version": "1.0"},
                },
            },
        )
        init_response.raise_for_status()
        init_payload = extract_jsonrpc_payload(
            init_response.headers.get("content-type", ""),
            init_response.text,
        )
        session_id = init_response.headers.get("mcp-session-id")

        headers = dict(base_headers)
        headers["mcp-protocol-version"] = PROTOCOL_VERSION
        if session_id:
            headers["mcp-session-id"] = session_id

        initialized_response = await client.post(
            url,
            headers=headers,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        if initialized_response.status_code >= 400:
            initialized_response.raise_for_status()

        tools_response = await client.post(
            url,
            headers=headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        tools_response.raise_for_status()
        tools_payload = extract_jsonrpc_payload(
            tools_response.headers.get("content-type", ""),
            tools_response.text,
        )
        tool_names = sorted(tool["name"] for tool in tools_payload["result"]["tools"])

        safe_call_payload = await _call_tool(
            client,
            url,
            headers,
            3,
            "get_pet_context",
            {"pet_id": "pika-demo"},
        )

        approval_payload = await _call_tool(
            client,
            url,
            headers,
            4,
            "request_owner_approval",
            {
                "pet_id": "pika-demo",
                "action_type": "schedule_followup",
                "reason": "Follow up after a non-urgent home observation.",
                "owner_approved": True,
                "observation_text": "Pika had one soft stool but is alert and drinking.",
                "observation_tags": ["soft_stool"],
            },
        )
        approval_result = tool_result_payload(approval_payload)
        authorization_id = approval_result.get("authorization_id")

        outcome_payload = await _call_tool(
            client,
            url,
            headers,
            5,
            "record_followup_outcome",
            {
                "pet_id": "pika-demo",
                "action_type": "schedule_followup",
                "authorization_id": authorization_id,
                "record": "Demo follow-up scheduled after explicit owner approval.",
            },
        )
        outcome_result = tool_result_payload(outcome_payload)

        replay_payload = await _call_tool(
            client,
            url,
            headers,
            6,
            "record_followup_outcome",
            {
                "pet_id": "pika-demo",
                "action_type": "schedule_followup",
                "authorization_id": authorization_id,
                "record": "Replay attempt must fail closed.",
            },
        )

        red_flag_payload = await _call_tool(
            client,
            url,
            headers,
            7,
            "request_owner_approval",
            {
                "pet_id": "pika-demo",
                "action_type": "schedule_followup",
                "reason": "Attempt ordinary follow-up despite red flags.",
                "owner_approved": True,
                "observation_text": "Pika collapsed and has difficulty breathing.",
                "observation_tags": ["collapse", "difficulty_breathing"],
            },
        )
        red_flag_result = tool_result_payload(red_flag_payload)

        escalation_payload = await _call_tool(
            client,
            url,
            headers,
            8,
            "escalate_to_professional",
            {
                "pet_id": "pika-demo",
                "reason": "collapse + difficulty_breathing",
            },
        )
        escalation_result = tool_result_payload(escalation_payload)

    scenario_a_ok = bool(
        approval_result.get("authorized") is True
        and authorization_id
        and outcome_result.get("executed") is True
        and tool_call_failed_closed(replay_payload)
    )
    scenario_b_ok = bool(
        red_flag_result.get("authorized") is False
        and red_flag_result.get("action_class") == "PROFESSIONAL_ESCALATION"
        and not red_flag_result.get("authorization_id")
        and escalation_result.get("action_class") == "PROFESSIONAL_ESCALATION"
        and escalation_result.get("executed") is False
    )

    return {
        "ok": bool(
            "result" in init_payload
            and "result" in tools_payload
            and "result" in safe_call_payload
            and scenario_a_ok
            and scenario_b_ok
        ),
        "service_auth_enabled": bool(service_token),
        "protocol_version": init_payload.get("result", {}).get("protocolVersion"),
        "session_assigned": bool(session_id),
        "registered_tools": tool_names,
        "tool_count": len(tool_names),
        "safe_tool_call_ok": "result" in safe_call_payload,
        "scenario_a_owner_approval_receipt_outcome_replay_guard": scenario_a_ok,
        "scenario_b_red_flag_escalation_override_guard": scenario_b_ok,
        "replay_rejected": tool_call_failed_closed(replay_payload),
        "red_flag_action_class": red_flag_result.get("action_class"),
    }
