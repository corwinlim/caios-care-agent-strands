from src.protocol_helpers import tool_result_payload, tool_call_failed_closed


def test_structured_content_preferred():
    payload = tool_result_payload({
        "result": {
            "structuredContent": {"authorized": True, "authorization_id": "abc"},
            "content": [{"type": "text", "text": "ignored"}],
        }
    })
    assert payload["authorization_id"] == "abc"


def test_text_json_fallback():
    payload = tool_result_payload({
        "result": {
            "content": [{"type": "text", "text": '{"executed":true}'}]
        }
    })
    assert payload["executed"] is True


def test_error_result_counts_as_fail_closed():
    assert tool_call_failed_closed({"result": {"isError": True}}) is True
    assert tool_call_failed_closed({"error": {"code": -32603}}) is True
    assert tool_call_failed_closed({"result": {"isError": False}}) is False


def test_structured_rejection_counts_as_fail_closed():
    message = {
        "result": {
            "structuredContent": {
                "executed": False,
                "error": "authorization_receipt_invalid_or_used",
            },
            "isError": False,
        }
    }
    assert tool_call_failed_closed(message) is True
