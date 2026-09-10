import importlib


def test_mcp_server_exposes_required_tool_names():
    module = importlib.import_module("src.mcp_server")
    assert module.REQUIRED_TOOL_NAMES == {
        "get_pet_context",
        "record_home_observation",
        "propose_followup_action",
        "request_owner_approval",
        "record_followup_outcome",
        "escalate_to_professional",
    }


def test_mcp_server_exports_asgi_app():
    module = importlib.import_module("src.mcp_server")
    assert module.app is not None
