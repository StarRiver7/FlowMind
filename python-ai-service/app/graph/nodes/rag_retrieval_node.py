"""RAG Retrieval Node — LangGraph node for knowledge base retrieval.

Flow:
  1. Build retrieval context from user query + permissions
  2. Execute full retrieval pipeline (rewrite → dense → sparse → fuse → ... → context)
  3. Populate state with RAG context and sources
  4. Route to answer_node for response generation

Integrates with the new RetrievalPipeline for enterprise-grade retrieval.
"""

import time
from typing import Optional
from datetime import datetime, timezone

from app.graph.state import InternState
from app.rag.retrieval.retriever import retriever, RetrievalResult
from app.rag.permission_filter import permission_filter
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


async def rag_retrieval_node(state: InternState) -> InternState:
    """RAG retrieval node for LangGraph.

    Reads: state["user_message"], permission_context, space_ids
    Writes: state["retrieved_docs"], state["rag_context"], state["sources"]

    The retrieval pipeline runs:
      query → rewrite → dense → sparse → fuse → boost → rerank → merge → context
    and each step is traced in state["trace_steps"].
    """
    t0 = time.time()
    state["current_node"] = "rag_retrieval_node"

    # Start trace
    state["trace_steps"] = state.get("trace_steps", []) + [{
        "node": "rag_retrieval_node",
        "message": "正在搜索企业知识库...",
        "status": "running",
        "timestamp": _now(),
    }]

    query = state["user_message"]
    user_id = _to_int(state.get("user_id", "0"))
    permission_ctx = state.get("permission_context", {})
    department_id = permission_ctx.get("department_id")
    space_ids = state.get("space_ids") or permission_ctx.get("allowed_space_ids") or []

    # Collect stream traces for SSE
    stream_traces: list[dict] = []

    try:
        # Execute full retrieval pipeline
        result: RetrievalResult = await retriever.retrieve(
            query=query,
            top_k=settings.rag_top_k,
            final_k=settings.rag_final_k,
            score_threshold=settings.rag_score_threshold,
            user_id=user_id,
            department_id=department_id,
            space_ids=space_ids,
            stream_traces=stream_traces,
        )

        hit_count = result.final_count

        # Apply permission filter (extra safety layer)
        chunks = result.merged_chunks
        if permission_ctx and chunks:
            filtered = permission_filter.filter_chunks(
                chunks=chunks,
                user_id=str(user_id),
                department_id=department_id or 0,
                department_path=permission_ctx.get("department_path", ""),
                allowed_space_ids=space_ids,
            )
        else:
            filtered = chunks

        # Populate state
        state["retrieved_docs"] = filtered
        state["filtered_docs"] = filtered
        state["rag_context"] = result.context_text
        state["sources"] = result.sources

        # Map pipeline traces to LangGraph trace_steps format
        _trace_map = {
            "rewrite_query": "正在优化查询...",
            "dense_retrieval": "正在进行语义检索...",
            "sparse_retrieval": "正在进行关键词检索...",
            "score_fusion": "正在融合检索结果...",
            "metadata_boost": "正在优化排序...",
            "rerank": "正在重排序知识片段...",
            "chunk_merge": "正在合并上下文...",
            "source_builder": "正在构建引用信息...",
            "context_builder": "正在组织知识内容...",
        }

        for trace in result.traces:
            step_name = trace.get("step", "")
            detail = trace.get("detail", {})
            if step_name in _trace_map:
                state["trace_steps"].append({
                    "node": "rag_retrieval_node",
                    "message": _trace_map[step_name],
                    "status": "completed",
                    "detail": detail,
                    "sub_step": step_name,
                    "timestamp": _now(),
                })

        duration_ms = int((time.time() - t0) * 1000)

        # Complete the main trace
        state["trace_steps"][-1] = {
            "node": "rag_retrieval_node",
            "message": f"已检索到 {len(filtered)} 条相关知识",
            "status": "completed",
            "detail": {
                "dense_count": result.dense_count,
                "sparse_count": result.sparse_count,
                "fused_count": result.fused_count,
                "final_count": len(filtered),
                "truncated": result.truncated,
                "elapsed_ms": result.elapsed_ms,
            },
            "duration_ms": duration_ms,
            "timestamp": _now(),
        }

        logger.info(
            f"[RAGNode] '{query[:40]}': {len(filtered)} chunks, "
            f"{len(result.sources)} sources in {duration_ms}ms"
        )

    except Exception as e:
        logger.warning(f"RAG retrieval failed (continuing without): {e}")
        duration_ms = int((time.time() - t0) * 1000)

        state["retrieved_docs"] = []
        state["filtered_docs"] = []
        state["rag_context"] = (
            "收到老师～我刚刚搜索知识库时遇到一点问题，请稍后再试～"
        )
        state["sources"] = []

        state["trace_steps"][-1] = {
            "node": "rag_retrieval_node",
            "message": "知识检索暂时不可用",
            "status": "failed",
            "detail": {"error": str(e)[:200]},
            "duration_ms": duration_ms,
            "timestamp": _now(),
        }

    return state


def _to_int(value) -> int:
    """Safely convert to int."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
