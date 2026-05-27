"""RAG Answer Node — retrieval → rerank → citation → answer generation.

Full pipeline:
  1. Retrieve: hybrid search + rerank + citation build
  2. Build: citation-aware context prompt
  3. Generate: LLM answer with inline citations [来源N]
  4. Highlight: map citations back to answer text spans
  5. Format: frontend-ready response with citations

Trustworthiness rules:
  - If recall is empty or scores too low → refuse to fabricate
  - Every claim must be traceable to a source
  - Unsupported claims are flagged
"""

import time
from datetime import datetime, timezone

from app.graph.state import InternState
from app.rag.retrieval.retriever import retriever, RetrievalResult
from app.rag.citation.citation_builder import citation_builder
from app.rag.citation.source_formatter import source_formatter
from app.rag.citation.source_highlighter import source_highlighter
from app.rag.citation.citation_models import CitationSet
from app.rag.permission_filter import permission_filter
from app.llm.gateway import llm_gateway
from app.prompts.internsu_prompts import (
    InternSUPrompts, PromptType, SYSTEM_PROMPT,
)
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# ── Citation-Aware RAG Answer Prompt ──
RAG_ANSWER_PROMPT = """你是小SU，一个刚入职的AI实习生，同事们都叫你"小SU"。

## 任务
老师问了一个问题，你需要根据下面的公司资料来回答。

## 公司资料（含引用来源）
{rag_context}

## 回答规则（必须严格遵守）
1. **只根据资料回答**：不要使用你自己的知识
2. **必须标注来源**：使用 [来源N] 格式标注每个引用的来源
3. **诚实原则**：
   - 如果资料中没有相关信息，说"老师，我在公司资料里没有找到相关信息～"
   - 如果资料信息不完整，说明"老师，根据现有资料，我只能确认..."
   - 不要编造任何不在资料中的内容
4. **引用格式示例**：
   - 根据《员工手册》，年假需提前3天申请[来源1]
   - 考勤制度规定每日打卡时间为9:00前[来源2]
5. **回答结构**：
   - 以"收到老师～"开头
   - 简洁回答老师的问题
   - 多用资料中的原文
   - 在回答末尾列出参考来源列表

## 老师的问题
{user_message}

## 你的回答（按规则回答，标注 [来源N]）"""

# ── Fallback prompt when retrieval fails ──
RAG_NO_RESULTS_PROMPT = """你是小SU，一个刚入职的AI实习生。

老师问了一个问题：{user_message}

但是你在公司知识库中没有找到足够可靠的相关信息。

请以"收到老师～"开头，诚实地告诉老师：
- 你在知识库中没有找到相关信息
- 建议老师尝试换个说法或者联系相关部门
- 不要编造任何内容

你的回答："""


async def rag_answer_node(state: InternState) -> InternState:
    """RAG Answer Node — complete retrieval-to-answer pipeline.

    Reads: user_message, permission_context, space_ids
    Writes: final_answer, sources, citation_set, rag_context
    """
    t0 = time.time()
    state["current_node"] = "rag_answer_node"

    state["trace_steps"] = state.get("trace_steps", []) + [{
        "node": "rag_answer_node",
        "message": "正在搜索企业知识库...",
        "status": "running",
        "timestamp": _now(),
    }]

    query = state["user_message"]
    user_id = _to_int(state.get("user_id", "0"))
    permission_ctx = state.get("permission_context", {})
    department_id = permission_ctx.get("department_id")
    space_ids = state.get("space_ids") or permission_ctx.get("allowed_space_ids") or []
    model = state.get("model_name", "deepseek-chat")

    stream_traces: list[dict] = []

    try:
        # ── Step 1: Full Retrieval + Rerank + Citation ──
        _add_trace(state, "正在进行语义检索与重排序...")
        result: RetrievalResult = await retriever.retrieve(
            query=query,
            top_k=settings.rag_top_k,
            final_k=settings.rag_final_k,
            score_threshold=settings.rag_score_threshold,
            user_id=user_id,
            department_id=department_id,
            space_ids=space_ids,
            stream_traces=stream_traces,
            enable_citation=True,
        )

        # Permission filter (extra safety)
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

        state["retrieved_docs"] = filtered
        state["sources"] = result.sources

        # ── Step 2: Trust Check ──
        trust_level = result.trust_level
        citation_set = result.citation_set

        if not filtered or trust_level == "unreliable":
            # No reliable results → refuse to fabricate
            _add_trace(state, "知识库中未找到足够可靠的信息")
            answer = await _generate_no_results(query, model)
            state["final_answer"] = answer
            state["rag_context"] = ""
            state["sources"] = []
            _finish_trace(state, "已告知老师未找到相关信息", t0)
            return state

        # ── Step 3: Build Citation-Aware Prompt ──
        _add_trace(state, "正在整理引用来源...")
        rag_context = result.context_text if result.context_text else _build_fallback_context(filtered)

        prompt = RAG_ANSWER_PROMPT.format(
            rag_context=rag_context,
            user_message=query,
        )
        state["rag_context"] = rag_context

        # ── Step 4: Generate Answer ──
        _add_trace(state, "正在生成可信回答...")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        resp = await llm_gateway.chat(messages, model=model, temperature=0.5, max_tokens=2048)
        answer = resp.content.strip()
        state["tokens_used"] = state.get("tokens_used", 0) + (
            resp.usage.get("total_tokens", 0) if resp.usage else 0
        )
        state["final_answer"] = answer

        # ── Step 5: Citation Highlight Map ──
        if citation_set and citation_set.citations:
            highlight_map = source_highlighter.build_highlight_map(
                answer, citation_set.citations,
            )
            state["citation_highlights"] = highlight_map

        # ── Step 6: Format frontend response ──
        if citation_set:
            frontend = source_formatter.format_frontend_response(answer, citation_set)
            state["citation_set"] = frontend

        duration_ms = int((time.time() - t0) * 1000)
        _finish_trace(state, f"已基于{citation_set.count if citation_set else 0}条来源生成回答", t0)

        logger.info(
            f"[RAGAnswerNode] '{query[:40]}': "
            f"{result.final_count} chunks, "
            f"{citation_set.count if citation_set else 0} citations, "
            f"trust={trust_level}, {duration_ms}ms"
        )

    except Exception as e:
        logger.error(f"RAG answer generation failed: {e}")
        duration_ms = int((time.time() - t0) * 1000)
        state["final_answer"] = "收到老师～我刚刚整理回答时遇到一点问题，请稍后重试～"
        state["rag_context"] = ""
        state["sources"] = []
        state["error"] = str(e)[:200]

        state["trace_steps"][-1] = {
            "node": "rag_answer_node",
            "message": "回答生成暂时不可用",
            "status": "failed",
            "detail": {"error": str(e)[:200]},
            "duration_ms": duration_ms,
            "timestamp": _now(),
        }

    return state


async def _generate_no_results(query: str, model: str) -> str:
    """Generate honest 'no results' response."""
    try:
        prompt = RAG_NO_RESULTS_PROMPT.format(user_message=query)
        resp = await llm_gateway.chat(
            [{"role": "user", "content": prompt}],
            model=model, temperature=0.5, max_tokens=512,
        )
        return resp.content.strip()
    except Exception:
        return "收到老师～我在公司知识库中没有找到相关信息，建议您换个说法试试，或者联系相关部门确认～"


def _build_fallback_context(chunks: list[dict]) -> str:
    """Build simple context when citation set is unavailable."""
    parts = ["## 知识库检索结果"]
    for i, c in enumerate(chunks):
        name = c.get("document_name", "unknown")
        page = c.get("page_number", 0)
        content = c.get("content", "")
        parts.append(f"\n---\n[来源{i+1}] {name}" + (f" 第{page}页" if page else ""))
        parts.append(content[:800])
    return "\n".join(parts)


def _add_trace(state: InternState, message: str):
    state["trace_steps"] = state.get("trace_steps", []) + [{
        "node": "rag_answer_node",
        "message": message,
        "status": "running",
        "timestamp": _now(),
    }]


def _finish_trace(state: InternState, message: str, t0: float):
    duration_ms = int((time.time() - t0) * 1000)
    if state.get("trace_steps"):
        state["trace_steps"][-1] = {
            "node": "rag_answer_node",
            "message": message,
            "status": "completed",
            "duration_ms": duration_ms,
            "timestamp": _now(),
        }


def _to_int(value) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
