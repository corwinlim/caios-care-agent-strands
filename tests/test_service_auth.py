import base64

from src.service_auth import ServiceAuth


def basic(client_id: str, secret: str) -> str:
    token = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    return f"Basic {token}"


def test_client_credentials_happy_path_and_bearer_validation():
    auth = ServiceAuth(
        client_id="alexa-client",
        client_secret="top-secret",
        resource="https://example.com/mcp",
        token_ttl_seconds=60,
    )
    token = auth.issue_client_credentials_token(
        authorization=basic("alexa-client", "top-secret"),
        grant_type="client_credentials",
        scope="mcp:service",
        resource="https://example.com/mcp",
    )
    assert token["token_type"] == "Bearer"
    assert token["scope"] == "mcp:service"
    assert auth.validate_bearer(f"Bearer {token['access_token']}") is True


def test_rejects_wrong_resource():
    auth = ServiceAuth(
        client_id="alexa-client",
        client_secret="top-secret",
        resource="https://example.com/mcp",
    )
    try:
        auth.issue_client_credentials_token(
            authorization=basic("alexa-client", "top-secret"),
            grant_type="client_credentials",
            scope="mcp:service",
            resource="https://evil.example/mcp",
        )
    except ValueError as exc:
        assert str(exc) == "invalid_resource"
    else:
        raise AssertionError("wrong resource must fail")


def test_rejects_user_scope_for_client_credentials():
    auth = ServiceAuth(
        client_id="alexa-client",
        client_secret="top-secret",
        resource="https://example.com/mcp",
    )
    try:
        auth.issue_client_credentials_token(
            authorization=basic("alexa-client", "top-secret"),
            grant_type="client_credentials",
            scope="mcp:tools",
            resource="https://example.com/mcp",
        )
    except ValueError as exc:
        assert str(exc) == "invalid_scope"
    else:
        raise AssertionError("user scope must fail")
