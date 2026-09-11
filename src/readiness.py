async def readiness_snapshot(server, required_tool_names: set[str]) -> dict:
    tools = await server.list_tools()
    registered = sorted(tool.name for tool in tools)
    missing = sorted(required_tool_names.difference(registered))
    return {
        "ready": not missing,
        "registered_tools": registered,
        "missing_tools": missing,
    }
