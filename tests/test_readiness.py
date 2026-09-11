import asyncio

from src.readiness import readiness_snapshot


class Tool:
    def __init__(self, name):
        self.name = name


class FakeServer:
    async def list_tools(self):
        return [Tool("a"), Tool("b")]


def test_ready_when_exact_tools_registered():
    snapshot = asyncio.run(readiness_snapshot(FakeServer(), {"a", "b"}))
    assert snapshot == {"ready": True, "registered_tools": ["a", "b"], "missing_tools": []}


def test_not_ready_when_required_tool_missing():
    snapshot = asyncio.run(readiness_snapshot(FakeServer(), {"a", "b", "c"}))
    assert snapshot["ready"] is False
    assert snapshot["missing_tools"] == ["c"]
