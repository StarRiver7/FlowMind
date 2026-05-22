import math
from app.tools.base_tool import BaseTool, ToolDefinition


class CalculatorTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calculator",
            description="Evaluate a mathematical expression. Supports +, -, *, /, **, sqrt, sin, cos, log.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate, e.g. '2 + 3 * 4'",
                    }
                },
                "required": ["expression"],
            },
        )

    async def execute(self, expression: str = "") -> str:
        allowed = set("0123456789+-*/().% eExXpiPIinsSqrtTqQcCoOaAlLnNgG")
        if not all(c in allowed for c in expression):
            return "Error: expression contains disallowed characters"

        try:
            namespace = {"__builtins__": None, "math": math}
            result = eval(expression, namespace)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
