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
    return bool(message.get("result", {}).get("isError"))
