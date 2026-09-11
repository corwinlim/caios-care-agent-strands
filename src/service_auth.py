from __future__ import annotations

import base64
import secrets
import time


class ServiceAuth:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        resource: str,
        token_ttl_seconds: int = 3600,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.resource = resource
        self.token_ttl_seconds = min(int(token_ttl_seconds), 3600)
        self._tokens: dict[str, float] = {}

    def _validate_basic(self, authorization: str) -> None:
        if not authorization.startswith("Basic "):
            raise ValueError("invalid_client")
        try:
            raw = base64.b64decode(authorization[6:]).decode("utf-8")
            client_id, client_secret = raw.split(":", 1)
        except Exception as exc:
            raise ValueError("invalid_client") from exc
        if not (
            secrets.compare_digest(client_id, self.client_id)
            and secrets.compare_digest(client_secret, self.client_secret)
        ):
            raise ValueError("invalid_client")

    def issue_client_credentials_token(
        self,
        *,
        authorization: str,
        grant_type: str,
        scope: str,
        resource: str,
    ) -> dict:
        self._validate_basic(authorization)
        if grant_type != "client_credentials":
            raise ValueError("unsupported_grant_type")
        if resource != self.resource:
            raise ValueError("invalid_resource")
        if scope != "mcp:service":
            raise ValueError("invalid_scope")

        access_token = secrets.token_urlsafe(32)
        self._tokens[access_token] = time.time() + self.token_ttl_seconds
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.token_ttl_seconds,
            "scope": "mcp:service",
        }

    def validate_bearer(self, authorization: str) -> bool:
        if not authorization.startswith("Bearer "):
            return False
        token = authorization[7:]
        expires_at = self._tokens.get(token)
        if expires_at is None or expires_at <= time.time():
            self._tokens.pop(token, None)
            return False
        return True
