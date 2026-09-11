from src.protocol_selftest import extract_jsonrpc_payload


def test_extracts_json_response():
    assert extract_jsonrpc_payload(
        "application/json",
        '{"jsonrpc":"2.0","id":1,"result":{"ok":true}}',
    )["result"]["ok"] is True


def test_extracts_sse_data_response():
    payload = extract_jsonrpc_payload(
        "text/event-stream",
        'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}\n\n',
    )
    assert payload["result"]["tools"] == []
