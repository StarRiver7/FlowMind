
"""RAG 检索节点 - 搜索企业知识库。

流程:
  1. 查询重写 (可选)
  2. Milvus 向量检索 + BM25 关键词检索
  3. RRF 融合 + Reranker 重排序
  4. 权限过滤 (private/department/public)
  5. 构建 RAG 上下文 (含 Source 信息)
"""

import time
from app.graph.state import InternState
from app.pipeline.rag_pipeline import rag_pipeline
from app.rag.permission_filter import permission_filter
from app.prompts.internsu_prompts import InternSUPrompts, PromptType
from app.core.logger import get_logger

logger = get_logger(__name__)


async def rag_node(state: InternState) -> InternState:
    """RAG 检索节点。"""
    step_start = time.time()
    state["traces"] = state.get("traces", []) + [{
        "step": "knowledge_retrieval",
        "status": "running",
        "step_order": 2,
    }]

    query = state["message"]
    permission_ctx = state.get("permission_context", {})
    user_id = state.get("user_id", "0")

    try:
        # Step 1: 检索 (混合搜索 + Reranking)
        raw_chunks = await rag_pipeline.search(
            query=query,
            top_k=10,
            use_rerank=True,
            with_citation=True,
        )
        hit_count = len(raw_chunks)
        logger.debug(f"RAG raw hits: {hit_count}")

        # Step 2: 权限过滤
        if permission_ctx:
            filtered = permission_filter.filter_chunks(
                chunks=raw_chunks,
                user_id=user_id,
                department_id=permission_ctx.get("department_id", 0),
                department_path=permission_ctx.get("department_path", ""),
                allowed_space_ids=permission_ctx.get("allowed_space_ids", []),
            )
        else:
            filtered = raw_chunks

        state["retrieved_docs"] = filtered
        state["filtered_docs"] = filtered

        # Step 3: 构建 RAG 上下文 + Source 引用
        sources = []
        context_parts = []

        for i, chunk in enumerate(filtered):
            meta = chunk.get("metadata", {})
            file_name = meta.get("file_name", "unknown")
            page_number = meta.get("page_number", None)
            content = chunk.get("content", "")
            score = chunk.get("rerank_score") or chunk.get("score", 0)

            sources.append({
                "document_id": meta.get("document_id", 0),
                "document_name": file_name,
                "chunk_index": meta.get("chunk_index", i),
                "page_number": page_number,
                "excerpt": content[:200],
                "score": round(score, 4),
            })

            context_parts.append({
                "file_name": file_name,
                "page_number": page_number or "未知",
                "content": content,
            })

        state["sources"] = sources

        # 用 Jinja2 渲染 RAG 上下文
        rag_context = InternSUPrompts.render(
            PromptType.RAG,
            context_docs=context_parts,
            user_message=query,
        ) if filtered else ""

        state["rag_context"] = rag_context

        duration_ms = int((time.time() - step_start) * 1000)
        state["traces"][-1] = {
            "step": "knowledge_retrieval",
            "status": "completed",
            "step_order": 2,
            "detail": {
                "hit_count": hit_count,
                "filtered_count": len(filtered),
            },
            "duration_ms": duration_ms,
        }

    except Exception as e:
        logger.warning(f"RAG retrieval failed (continuing without): {e}")
        state["retrieved_docs"] = []
        state["filtered_docs"] = []
        state["sources"] = []
        state["rag_context"] = ""
        state["traces"][-1] = {
            "step": "knowledge_retrieval",
            "status": "failed",
            "step_order": 2,
            "detail": {"error": str(e)},
            "duration_ms": int((time.time() - step_start) * 1000),
        }

    return state
