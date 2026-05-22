import json
from typing import AsyncIterator
from app.core.config import settings
from app.llm.model_factory import llm_gateway
from app.llm.prompt_builder import prompt_builder
from app.rag.retriever.retriever import retriever_service
from app.tools.tool_registry import tool_registry
from app.memory.conversation_memory import memory_manager
from app.agents.base_agent import intent_router, IntentType
from app.common.exceptions.exceptions import AIServiceException


class AgentExecutor:
    """Agent执行器 — ReAct循环 + Tool Calling"""

    def __init__(self):
        self._max_iterations = settings.agent_max_iterations

    async def chat(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        model: str | None = None,
        use_rag: bool = True,
        use_tools: bool = True,
    ) -> dict:
        history = await memory_manager.get_history(user_id, conversation_id)
        intent = intent_router.route(message)
        retrieved_docs = []

        if intent.intent == IntentType.KNOWLEDGE and use_rag:
            retrieved_docs = await retriever_service.search(message)
            if retrieved_docs:
                messages = prompt_builder.build_rag_prompt(message, retrieved_docs, history)
            else:
                messages = prompt_builder.build(message, history)
        else:
            messages = prompt_builder.build(message, history)

        response = await llm_gateway.chat(messages, model=model)

        # Tool Calling检测：如果LLM返回了function call指令，执行工具
        if use_tools:
            response = await self._handle_tool_calls(
                response, messages, model, user_id, conversation_id, history
            )

        await memory_manager.add_message(user_id, conversation_id, "user", message)
        await memory_manager.add_message(user_id, conversation_id, "assistant", response)

        return {
            "content": response,
            "conversation_id": conversation_id,
            "intent": intent.intent.value,
            "sources": retrieved_docs if retrieved_docs else None,
        }

    async def chat_stream(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        model: str | None = None,
        use_rag: bool = True,
        use_tools: bool = True,
    ) -> AsyncIterator[dict]:
        history = await memory_manager.get_history(user_id, conversation_id)
        intent = intent_router.route(message)
        retrieved_docs = []

        if intent.intent == IntentType.KNOWLEDGE and use_rag:
            retrieved_docs = await retriever_service.search(message)
            if retrieved_docs:
                messages = prompt_builder.build_rag_prompt(message, retrieved_docs, history)
            else:
                messages = prompt_builder.build(message, history)
        else:
            messages = prompt_builder.build(message, history)

        await memory_manager.add_message(user_id, conversation_id, "user", message)

        full_response = ""
        async for token in llm_gateway.chat_stream(messages, model=model):
            full_response += token
            yield {"content": token, "done": False, "conversation_id": conversation_id}

        # Tool Calling检测
        if use_tools:
            tool_result = await self._handle_tool_calls(
                full_response, messages, model, user_id, conversation_id, history
            )
            if tool_result != full_response:
                full_response = tool_result
                yield {"content": "\n[Tool: " + tool_result[:200] + "]", "done": False}

        await memory_manager.add_message(user_id, conversation_id, "assistant", full_response)

        yield {
            "content": "",
            "done": True,
            "conversation_id": conversation_id,
            "intent": intent.intent.value,
            "sources": retrieved_docs if retrieved_docs else None,
        }

    async def _handle_tool_calls(
        self,
        response: str,
        messages: list[dict],
        model: str | None,
        user_id: str,
        conversation_id: str,
        history: list[dict],
    ) -> str:
        """检测LLM响应中的工具调用指令并执行"""
        # 简单检测：如果响应中包含特定模式的工具调用标记
        # 生产环境应使用OpenAI function calling原生支持
        if "[TOOL:" in response:
            try:
                tool_part = response.split("[TOOL:")[1].split("]")[0]
                tool_name, _, tool_args = tool_part.partition("(")
                tool_args = tool_args.rstrip(")")

                params = {}
                if tool_args:
                    for pair in tool_args.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            params[k.strip()] = v.strip().strip("'").strip('"')

                exec_result = await tool_registry.execute(
                    name=tool_name.strip(),
                    user_id=int(user_id) if user_id else None,
                    conversation_id=int(conversation_id) if conversation_id else None,
                    **params,
                )
                return response.replace(f"[TOOL:{tool_part}]", exec_result.get("result", ""))

            except Exception:
                pass  # 工具调用失败，返回原始响应

        return response


agent_executor = AgentExecutor()
