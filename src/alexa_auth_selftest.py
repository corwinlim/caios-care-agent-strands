from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import httpx

PROTOCOL_VERSION = "2025-11-25"


async def run_alexa_auth_selftest(port: int) -> dict[str, Any]:
    await asyncio.sleep(0.9)
    base_url = os.environ.get("ALEXA_MCP_BASE_URL", "").rstrip("/")
    if not base_url:
        return {"ok": False, "configured": False, "reason": "base_url_missing"}

    local = f"http://127.0.0.1:{port}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        prm_response = await client.get(f"{local}/.well-known/oauth-protected-resource")
        prm_response.raise_for_status()
        prm = prm_response.json()

        metadata_response = await client.get(f"{local}/.well-known/oauth-authorization-server")
        metadata_response.raise_for_status()
        metadata = metadata_response.json()

        unauth_response = await client.post(
            f"{local}/mcp",
            headers={
                "content-type": "application/json",
                "accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "id": "auth-probe",
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "caios-auth-probe", "version": "1.0"},
                },
            },
        )

    expected_resource = f"{base_url}/mcp"
    prm_ok = bool(
        prm.get("resource") == expected_resource
        and base_url in prm.get("authorization_servers", [])
        and "mcp:service" in prm.get("scopes_supported", [])
    )
    metadata_ok = bool(
        metadata.get("issuer") == base_url
        and metadata.get("token_endpoint") == f"{base_url}/oauth/token"
        and "client_credentials" in metadata.get("grant_types_supported", [])
        and "S256" in metadata.get("code_challenge_methods_supported", [])
    )
    unauth_ok = bool(
        unauth_response.status_code == 401
        and "www-authenticate" not in {key.lower() for key in unauth_response.headers.keys()}
    )

    return {
        "ok": prm_ok and metadata_ok and unauth_ok,
        "configured": True,
        "prm_ok": prm_ok,
        "oauth_metadata_ok": metadata_ok,
        "pkce_s256_declared": "S256" in metadata.get("code_challenge_methods_supported", []),
        "unauthenticated_mcp_is_401": unauth_response.status_code == 401,
        "www_authenticate_absent": "www-authenticate" not in {key.lower() for key in unauth_response.headers.keys()},
    }
