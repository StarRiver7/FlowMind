import pytest
from app.tools.tool_registry import ToolRegistry
from app.common.exceptions.exceptions import ToolException


class TestToolRegistry:
    def setup_method(self):
        self.registry = ToolRegistry()

    def test_list_tools_has_calculator(self):
        tools = self.registry.list_tools()
        tool_names = [t["name"] for t in tools]
        assert "calculator" in tool_names

    def test_list_tools_has_web_search(self):
        tools = self.registry.list_tools()
        tool_names = [t["name"] for t in tools]
        assert "web_search" in tool_names

    def test_get_all_definitions_format(self):
        defs = self.registry.get_all_definitions()
        assert len(defs) >= 2
        for d in defs:
            assert "type" in d
            assert d["type"] == "function"
            assert "function" in d
            assert "name" in d["function"]

    def test_get_existing_tool(self):
        tool = self.registry.get("calculator")
        assert tool is not None
        assert tool.definition.name == "calculator"

    def test_get_nonexistent_tool_raises(self):
        with pytest.raises(ToolException, match="Tool not found"):
            self.registry.get("nonexistent_tool")

    @pytest.mark.asyncio
    async def test_execute_calculator(self):
        result = await self.registry.execute("calculator", expression="2+3")
        assert result["success"] is True
        assert "5" in result["result"]
