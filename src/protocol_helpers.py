import json


def tool_result_payload(message: dict) -> dict:
    result = message.get("result", {})
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        return structured
    for item in result.get("content", []):
        if item.get("type") == "text":
            try:
                payload = json.loads(item.get("text", ""))
            except Exception:
                continue
            if isinstance(payload, dict):
                return payload
    return {}


def tool_call_failed_closed(message: dict) -> bool:
    if "error" in message:
        return True
    result = message.get("result", {})
    if result.get("isError"):
        return True
    payload = tool_result_payload(message)
    return payload.get("executed") is False and bool(payload.get("error"))
