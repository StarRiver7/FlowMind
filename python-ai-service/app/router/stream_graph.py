"""Streaming LangGraph orchestrator — real-time token streaming through the router.

Flow:
    1. classify_intent (non-streaming, fast)
    2. rag_node / tool_node (non-streaming, fast)
    3. chat_node_stream → yields tokens one at a time via DeepSeek streaming

This is separate from the non-streaming graph to keep concerns clean.
"""
import json
import re
from typing import AsyncIterator
from app.router.models import RouterState
from app.llm.gateway import llm_gateway
from app.prompt.manager import prompt_manager
from app.pipeline.rag_pipeline import rag_pipeline
from app.tools.registry import tool_registry
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class StreamOrchestrator:
    """Orchestrates the full AI pipeline with real-time token streaming."""

    # ---- Phase 1: Intent classification (fast, non-streaming) ----

    async def _classify_intent(self, message: str) -> str:
        """Classify user intent using lightweight LLM call."""
        messages = [
            {"role": "system", "content": (
                "Classify the user message into exactly one intent category. "
                "Respond with ONLY the category name: chat, rag, tool, or sql.\n"
                "- chat: casual conversation, general questions, greetings\n"
                "- rag: knowledge/document lookup, policy questions, how-to\n"
                "- tool: calculation, search, external action needed\n"
                "- sql: data queries, statistics, reporting, rankings"
            )},
            {"role": "user", "content": message},
        ]
        try:
            resp = await llm_gateway.chat(messages, temperature=0.0, max_tokens=10)
            intent = resp.content.strip().lower()
            if intent not in ("chat", "rag", "tool", "sql"):
                intent = "chat"
            logger.debug(f"Intent: {intent} for '{message[:50]}...'")
            return intent
        except Exception as e:
            logger.warning(f"Intent classification failed: {e}")
            return "chat"

    # ---- Phase 2: RAG retrieval (fast, non-streaming) ----

    async def _retrieve_docs(self, query: str, tenant_id: str = "default") -> list[dict]:
        """Retrieve relevant documents via hybrid search."""
        try:
            docs = await rag_pipeline.search(
                query=query,
                top_k=settings.rag_final_k,
                use_rerank=True,
                with_citation=True,
                tenant_id=tenant_id,
            )
            logger.debug(f"RAG retrieved {len(docs)} docs")
            return docs
        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            return []

    # ---- Phase 3: Tool execution (fast, non-streaming) ----

    async def _execute_tool(self, message: str) -> list[dict]:
        """Execute tool based on user message."""
        try:
            messages = [
                {"role": "system", "content": (
                    "Call the appropriate tool based on the user's request. "
                    'Respond in JSON: {"tool": "name", "params": {...}}'
                )},
                {"role": "user", "content": message},
            ]
            resp = await llm_gateway.chat(messages, temperature=0.0, max_tokens=256)

            json_match = re.search(r'\{[\s\S]*"tool"[\s\S]*\}', resp.content)
            if json_match:
                tool_call = json.loads(json_match.group())
                result = await tool_registry.execute(tool_call["tool"], **tool_call.get("params", {}))
                logger.info(f"Tool '{tool_call['tool']}' executed: success={result['success']}")
                return [result]
            return [{"success": False, "error": "Could not parse tool call"}]
        except Exception as e:
            logger.warning(f"Tool execution failed: {e}")
            return [{"success": False, "error": str(e)}]

    # ---- Phase 4: Streaming LLM response ----

    def _build_messages(
        self, intent: str, message: str, history: list[dict],
        retrieved_docs: list[dict], tool_results: list[dict],
    ) -> list[dict]:
        """Build the messages array for the final LLM call based on intent."""
        if intent == "rag" and retrieved_docs:
            context_str = "\n\n".join(
                f"[Source: {d.get('metadata', {}).get('file_name', 'doc')}] {d['content']}"
                for d in retrieved_docs
            )
            messages = [
                {"role": "system", "content": (
                    f"Answer based on the following context:\n\n{context_str}\n\n"
                    "Be concise and cite sources. Use [Source: filename] notation."
                )},
            ]
            if history:
                messages.extend(history[-settings.conversation_window * 2:])
            messages.append({"role": "user", "content": message})
        elif intent == "tool" and tool_results:
            tool_output = "\n".join(
                r.get("result", r.get("error", ""))
                for r in tool_results
            )
            messages = [
                {"role": "system", "content": f"Tool results:\n{tool_output}\n\nSummarize for the user."},
                {"role": "user", "content": message},
            ]
        else:
            messages = prompt_manager.build_messages(
                "default-system", message, history=history,
            )
        return messages

    async def stream_tokens(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream tokens from the LLM provider."""
        async for token in llm_gateway.chat_stream(
            messages, model=model, temperature=temperature,
        ):
            yield token

    # ---- Full streaming pipeline ----

    async def stream_chat(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        history: list[dict],
        use_rag: bool = True,
        use_tools: bool = True,
        model: str | None = None,
        tenant_id: str = "default",
    ) -> AsyncIterator[dict]:
        """Execute the full pipeline and stream results as structured events.

        Yields dicts with keys:
            - type: "thinking" | "token" | "done" | "error"
            - content: str (for thinking/token/error)
            - intent: str (for done)
            - sources: list[dict] (for done)
            - conversation_id: str (for done)
        """
        full_text = ""
        intent = "chat"
        retrieved_docs = []
        tool_results = []
        sources_out = []

        try:
            # Phase 1: Intent classification
            yield {"type": "thinking", "content": "Analyzing your request..."}
            if use_rag or use_tools:
                intent = await self._classify_intent(message)
            logger.info(f"Intent: {intent}")

            # Phase 2: RAG retrieval
            if use_rag and intent == "rag":
                yield {"type": "thinking", "content": "Searching knowledge base..."}
                retrieved_docs = await self._retrieve_docs(message, tenant_id)
                if retrieved_docs:
                    yield {"type": "thinking", "content": f"Found {len(retrieved_docs)} relevant documents"}

            # Phase 3: Tool execution
            if use_tools and intent == "tool":
                yield {"type": "thinking", "content": "Executing tool..."}
                tool_results = await self._execute_tool(message)

            # Phase 4: Streaming LLM response
            yield {"type": "thinking", "content": "Generating response..."}

            messages = self._build_messages(intent, message, history, retrieved_docs, tool_results)

            async for token in self.stream_tokens(messages, model=model):
                full_text += token
                yield {"type": "token", "content": token}

            # Build sources from retrieved docs
            for d in retrieved_docs:
                meta = d.get("metadata", {})
                sources_out.append({
                    "file": meta.get("file_name", ""),
                    "score": d.get("rerank_score") or d.get("score", 0),
                    "excerpt": d.get("excerpt", d.get("content", "")[:200]),
                })

            # Phase 5: Done
            yield {
                "type": "done",
                "intent": intent,
                "sources": sources_out,
                "conversation_id": conversation_id,
                "full_text": full_text,
            }

        except Exception as e:
            logger.error(f"Stream chat failed: {e}")
            yield {"type": "error", "content": str(e)}
            yield {
                "type": "done",
                "intent": intent,
                "sources": [],
                "conversation_id": conversation_id,
                "error": str(e),
            }


stream_orchestrator = StreamOrchestrator()