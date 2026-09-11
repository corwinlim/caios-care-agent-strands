from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import parse_qs

from .service_auth import ServiceAuth


def _headers(scope: dict) -> dict[str, str]:
    return {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


async def _body(receive: Any) -> bytes:
    chunks: list[bytes] = []
    while True:
        message = await receive()
        if message["type"] != "http.request":
            continue
        chunks.append(message.get("body", b""))
        if not message.get("more_body", False):
            return b"".join(chunks)


async def send_json(send: Any, status: int, payload: dict) -> None:
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(encoded)).encode()),
            (b"cache-control", b"no-store"),
        ],
    })
    await send({"type": "http.response.body", "body": encoded})


class AlexaServiceAuthApp:
    """OAuth service-auth wrapper for an MCP ASGI app.

    Tier 1 only: client_credentials protects service discovery and MCP traffic.
    User-level authorization_code + PKCE is intentionally not implemented here.
    """

    def __init__(self, downstream: Any) -> None:
        self.downstream = downstream
        self.base_url = os.environ.get("ALEXA_MCP_BASE_URL", "").rstrip("/")
        self.resource = f"{self.base_url}/mcp" if self.base_url else ""
        client_id = os.environ.get("ALEXA_MCP_CLIENT_ID", "")
        client_secret = os.environ.get("ALEXA_MCP_CLIENT_SECRET", "")
        self.enabled = bool(self.base_url and client_id and client_secret)
        self.auth = (
            ServiceAuth(
                client_id=client_id,
                client_secret=client_secret,
                resource=self.resource,
            )
            if self.enabled
            else None
        )

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.downstream(scope, receive, send)
            return

        path = scope.get("path", "")
        if path == "/.well-known/oauth-protected-resource":
            if not self.enabled:
                await send_json(send, 503, {"error": "service_auth_not_configured"})
                return
            await send_json(send, 200, {
                "resource": self.resource,
                "authorization_servers": [self.base_url],
                "scopes_supported": ["mcp:service"],
            })
            return

        if path == "/.well-known/oauth-authorization-server":
            if not self.enabled:
                await send_json(send, 503, {"error": "service_auth_not_configured"})
                return
            await send_json(send, 200, {
                "issuer": self.base_url,
                "token_endpoint": f"{self.base_url}/oauth/token",
                "grant_types_supported": ["client_credentials"],
                "token_endpoint_auth_methods_supported": ["client_secret_basic"],
                "scopes_supported": ["mcp:service"],
                "code_challenge_methods_supported": ["S256"],
            })
            return

        if path == "/oauth/token":
            if not self.enabled or self.auth is None:
                await send_json(send, 503, {"error": "service_auth_not_configured"})
                return
            if scope.get("method") != "POST":
                await send_json(send, 405, {"error": "method_not_allowed"})
                return
            headers = _headers(scope)
            form = parse_qs((await _body(receive)).decode("utf-8"))
            try:
                token = self.auth.issue_client_credentials_token(
                    authorization=headers.get("authorization", ""),
                    grant_type=form.get("grant_type", [""])[0],
                    scope=form.get("scope", [""])[0],
                    resource=form.get("resource", [""])[0],
                )
            except ValueError as exc:
                error = str(exc)
                status = 401 if error == "invalid_client" else 400
                await send_json(send, status, {"error": error})
                return
            await send_json(send, 200, token)
            return

        if path == "/mcp" and self.enabled:
            headers = _headers(scope)
            if self.auth is None or not self.auth.validate_bearer(headers.get("authorization", "")):
                # Alexa+ discovery expects 401 without WWW-Authenticate.
                await send_json(send, 401, {"error": "unauthorized"})
                return

        await self.downstream(scope, receive, send)
