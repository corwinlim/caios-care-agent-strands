from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

PROTOCOL_VERSION = "2025-11-25"


def extract_jsonrpc_payload(content_type: str, body: str) -> dict:
    if "text/event-stream" not in content_type:
        return json.loads(body)

    for line in body.splitlines():
        if line.startswith("data:"):
            return json.loads(line.split(":", 1)[1].strip())
    raise ValueError("no JSON-RPC data event found")


async def run_protocol_selftest(port: int) -> dict[str, Any]:
    """Exercise the deployed MCP wire path over localhost HTTP.

    This is startup evidence only. It never calls a consequential tool.
    """
    await asyncio.sleep(0.75)
    url = f"http://127.0.0.1:{port}/mcp"
    base_headers = {
        "content-type": "application/json",
        "accept": "application/json, text/event-stream",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
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

        call_response = await client.post(
            url,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_pet_context",
                    "arguments": {"pet_id": "pika-demo"},
                },
            },
        )
        call_response.raise_for_status()
        call_payload = extract_jsonrpc_payload(
            call_response.headers.get("content-type", ""),
            call_response.text,
        )

    return {
        "ok": "result" in init_payload and "result" in tools_payload and "result" in call_payload,
        "protocol_version": init_payload.get("result", {}).get("protocolVersion"),
        "session_assigned": bool(session_id),
        "registered_tools": tool_names,
        "tool_count": len(tool_names),
        "safe_tool_call_ok": "result" in call_payload,
    }
