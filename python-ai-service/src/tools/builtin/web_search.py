from src.tools.base import BaseTool, ToolDefinition


class WebSearchTool(BaseTool):
    """网页搜索工具 — 当前为降级实现，生产接入SerpAPI/Bing API"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_search",
            description="Search the web for real-time information. Returns top search results.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    }
                },
                "required": ["query"],
            },
        )

    async def execute(self, query: str = "") -> str:
        # TODO: 接入 SerpAPI / Bing Search API
        return f"[WebSearch] Results for: {query} (real API integration pending)"
