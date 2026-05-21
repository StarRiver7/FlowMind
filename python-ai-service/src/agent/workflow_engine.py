from typing import TypedDict, Annotated, Any
from operator import add
from src.config import settings


class WorkflowState(TypedDict):
    """LangGraph工作流状态"""
    input: str
    messages: Annotated[list[dict], add]
    current_step: str
    output: str
    error: str | None
    done: bool


class WorkflowEngine:
    """
    工作流引擎 — 基于状态机的工作流执行器
    生产环境接入LangGraph StateGraph实现完整DAG
    """

    def __init__(self):
        self._max_steps = 20

    async def execute(
        self,
        workflow_config: dict,
        input_data: dict,
    ) -> dict:
        """执行工作流 — 按节点排序顺序执行"""
        state: WorkflowState = {
            "input": str(input_data),
            "messages": [],
            "current_step": "start",
            "output": "",
            "error": None,
            "done": False,
        }

        nodes = workflow_config.get("nodes", [])
        sorted_nodes = sorted(nodes, key=lambda n: n.get("sort_order", 0))

        for step_num, node in enumerate(sorted_nodes):
            if step_num >= self._max_steps:
                state["error"] = "Max steps exceeded"
                break

            state["current_step"] = node.get("node_name", f"step_{step_num}")
            node_type = node.get("node_type", "llm")
            node_config = node.get("config", {})

            try:
                if node_type == "start":
                    continue
                elif node_type == "end":
                    state["done"] = True
                    break
                elif node_type == "llm":
                    result = await self._execute_llm_node(state, node_config)
                elif node_type == "tool":
                    result = await self._execute_tool_node(state, node_config)
                elif node_type == "condition":
                    result = await self._execute_condition_node(state, node_config)
                else:
                    result = f"Unknown node type: {node_type}"

                state["messages"].append({
                    "role": "workflow",
                    "step": state["current_step"],
                    "content": str(result),
                })

            except Exception as e:
                state["error"] = str(e)
                state["output"] = f"Workflow failed at {state['current_step']}: {e}"
                return state

        state["output"] = state["messages"][-1]["content"] if state["messages"] else "No output"
        state["done"] = True
        return state

    async def _execute_llm_node(self, state: WorkflowState, config: dict) -> str:
        from src.models.llm.llm_gateway import llm_gateway
        from src.prompts.builder import prompt_builder

        system_prompt = config.get("system_prompt", prompt_builder.DEFAULT_SYSTEM_PROMPT)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state["input"]},
        ]
        return await llm_gateway.chat(messages)

    async def _execute_tool_node(self, state: WorkflowState, config: dict) -> str:
        tool_name = config.get("tool_name", "")
        tool_params = config.get("tool_params", {})
        from src.tools.registry import tool_registry
        result = await tool_registry.execute(tool_name, **tool_params)
        return result.get("result", "Tool executed")

    async def _execute_condition_node(self, state: WorkflowState, config: dict) -> str:
        condition = config.get("condition", "")
        return f"Condition evaluated: {condition}"


workflow_engine = WorkflowEngine()
