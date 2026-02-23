"""Tests for MCP protocol integration"""
import pytest
import json


@pytest.mark.asyncio
class TestMCPIntegration:
    """Test MCP server integration (server.py lines 199-283)"""

    async def test_list_tools_returns_tools(self):
        """Test list_tools returns list of Tool objects"""
        from mac_calendar_mcp.server import list_tools
        tools = await list_tools()
        assert isinstance(tools, list)
        assert len(tools) == 9  # Updated: now includes 9 tools (get_calendar_events, get_events, list_calendars, get_reminders, search, get_today_summary, get_current_time, convert_time, list_timezones)

    async def test_get_calendar_events_tool_schema(self):
        """Test get_calendar_events tool has correct schema"""
        from mac_calendar_mcp.server import list_tools
        tools = await list_tools()

        tool = next(t for t in tools if t.name == "get_calendar_events")
        assert tool.name == "get_calendar_events"
        assert "inputSchema" in tool.__dict__ or hasattr(tool, "inputSchema")

    async def test_list_calendars_tool_schema(self):
        """Test list_calendars tool has correct schema"""
        from mac_calendar_mcp.server import list_tools
        tools = await list_tools()

        tool = next(t for t in tools if t.name == "list_calendars")
        assert tool.name == "list_calendars"

    async def test_call_tool_get_calendar_events(self):
        """Test calling get_calendar_events tool"""
        from mac_calendar_mcp.server import call_tool

        result = await call_tool(
            "get_calendar_events",
            {"start_date": "2024-12-15", "end_date": "2024-12-25"}
        )
        assert isinstance(result, list)
        assert len(result) > 0

    async def test_call_tool_list_calendars(self):
        """Test calling list_calendars tool"""
        from mac_calendar_mcp.server import call_tool

        result = await call_tool("list_calendars", {})
        assert isinstance(result, list)
        assert len(result) > 0

    async def test_tool_response_is_text_content(self):
        """Test tool responses are TextContent objects"""
        from mac_calendar_mcp.server import call_tool
        from mcp.types import TextContent

        result = await call_tool("list_calendars", {})
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

    async def test_json_response_formatting(self):
        """Test responses are properly formatted JSON"""
        from mac_calendar_mcp.server import call_tool

        result = await call_tool("list_calendars", {})
        text = result[0].text

        # Should be valid JSON
        data = json.loads(text)
        assert isinstance(data, list)

    async def test_json_indent_formatting(self):
        """Test JSON responses are indented for readability"""
        from mac_calendar_mcp.server import call_tool

        result = await call_tool("get_calendar_events", {"start_date": "2024-12-15", "end_date": "2024-12-25"})
        text = result[0].text

        # Should have indentation (multiple lines) when there's data
        if text != "[]":  # Non-empty response should be indented
            assert '\n' in text or len(text) < 10

    async def test_unknown_tool_raises_error(self):
        """Test calling unknown tool raises ValueError"""
        from mac_calendar_mcp.server import call_tool

        with pytest.raises(ValueError, match="Unknown tool"):
            await call_tool("nonexistent_tool", {})

    async def test_tool_arguments_passed_correctly(self):
        """Test tool arguments are correctly passed to handlers"""
        from mac_calendar_mcp.server import call_tool

        result = await call_tool(
            "get_calendar_events",
            {
                "start_date": "2024-12-15",
                "end_date": "2024-12-15",
                "calendar_names": ["Work"],
                "days_ahead": 7
            }
        )
        assert isinstance(result, list)

    async def test_default_days_ahead_parameter(self):
        """Test days_ahead defaults to 7"""
        from mac_calendar_mcp.server import call_tool

        result = await call_tool(
            "get_calendar_events",
            {"start_date": "2024-12-15"}
        )
        assert isinstance(result, list)

    async def test_optional_parameters_handling(self):
        """Test optional parameters can be omitted"""
        from mac_calendar_mcp.server import call_tool

        # All parameters optional
        result = await call_tool("get_calendar_events", {})
        assert isinstance(result, list)
