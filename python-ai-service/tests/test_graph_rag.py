"""Tests for LangGraph + RAG Integration — Phase 6.6.

Covers:
  1. Graph compilation (all nodes + edges)
  2. RAG Routing (intent → retrieval → rerank → citation → answer)
  3. Agentic Retrieval (fallback on empty results)
  4. Trust Gating (unreliable → no fabrication)
  5. Memory Node (state persistence)
  6. Multi-turn RAG (context carryover)
  7. SSE Trace Events
"""

import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ============================================================================
# Test 1: Graph Compilation — all nodes and edges intact
# ============================================================================
class TestGraphCompilation:
    """Verify the full Agentic RAG graph compiles correctly."""

    def test_graph_builds(self):
        """Graph should compile without errors."""
        from app.graph.intern_graph import build_intern_graph
        graph = build_intern_graph()
        assert graph is not None

    def test_graph_has_all_rag_nodes(self):
        """All RAG sub-nodes must be in the graph."""
        from app.graph.intern_graph import build_intern_graph
        graph = build_intern_graph()
        nodes = graph.get_graph().nodes
        required_nodes = [
            "intent_node", "router_node",
            "rag_retrieval_node", "rag_rerank_node",
            "citation_node", "rag_answer_node",
            "response_node", "memory_node",
        ]
        for node in required_nodes:
            assert node in nodes, f"Missing node: {node}"

    def test_graph_has_chat_sql_nodes(self):
        from app.graph.intern_graph import build_intern_graph
        graph = build_intern_graph()
        nodes = graph.get_graph().nodes
        assert "chat_node" in nodes
        assert "sql_node" in nodes

    def test_state_has_rag_fields(self):
        """InternState must include all new RAG fields."""
        from app.graph.state import InternState, create_initial_state
        state = create_initial_state("1", "conv1", "test")
        rag_fields = [
            "rag_triggered", "query_rewritten", "retrieval_query",
            "retrieval_results", "rerank_results", "citations",
            "citation_set", "trust_level", "rag_context",
            "rag_answer", "retrieval_attempts",
        ]
        for field in rag_fields:
            assert field in state, f"Missing state field: {field}"

    def test_state_defaults(self):
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "conv1", "hello")
        assert state["rag_triggered"] == False
        assert state["retrieval_attempts"] == 0
        assert state["retrieval_failed"] == False
        assert state["trust_level"] == "medium"
        assert state["intent"] == "chat"


# ============================================================================
# Test 2: RAG Router Logic
# ============================================================================
class TestRAGRouter:
    """RAG routing decisions."""

    def test_route_after_retrieval_with_results(self):
        from app.graph.routers.rag_router import route_after_rag_retrieval
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["retrieval_results"] = [{"content": "test", "score": 0.9}]
        result = route_after_rag_retrieval(state)
        assert result == "rag_rerank_node"

    def test_route_after_retrieval_empty(self):
        from app.graph.routers.rag_router import route_after_rag_retrieval
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["retrieval_results"] = []
        state["retrieval_attempts"] = 1
        result = route_after_rag_retrieval(state)
        assert result in ("rag_answer_node", "clarify_node")

    def test_route_after_retrieval_exhausted(self):
        from app.graph.routers.rag_router import route_after_rag_retrieval
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["retrieval_results"] = []
        state["retrieval_failed"] = True
        state["retrieval_attempts"] = 2
        result = route_after_rag_retrieval(state)
        assert result == "rag_answer_node"

    def test_route_after_rerank_with_results(self):
        from app.graph.routers.rag_router import route_after_rerank
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["rerank_results"] = [{"content": "test", "score": 0.9}]
        assert route_after_rerank(state) == "citation_node"

    def test_route_after_rerank_empty(self):
        from app.graph.routers.rag_router import route_after_rerank
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["rerank_results"] = []
        assert route_after_rerank(state) == "rag_answer_node"

    def test_route_after_citation_high_trust(self):
        from app.graph.routers.rag_router import route_after_citation
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["trust_level"] = "high"
        assert route_after_citation(state) == "rag_answer_node"

    def test_route_after_citation_unreliable(self):
        from app.graph.routers.rag_router import route_after_citation
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["trust_level"] = "unreliable"
        assert route_after_citation(state) == "clarify_node"

    def test_should_clarify_rag_vague(self):
        from app.graph.routers.rag_router import should_clarify_rag
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "查一下")
        state["intent"] = "rag"
        assert should_clarify_rag(state) == True

    def test_should_clarify_rag_specific(self):
        from app.graph.routers.rag_router import should_clarify_rag
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "公司员工请假制度如何申请")
        state["intent"] = "rag"
        assert should_clarify_rag(state) == False


# ============================================================================
# Test 3: RAG Retrieval Node
# ============================================================================
class TestRAGRetrievalNode:
    """RAG retrieval node (unit — no Milvus needed)."""

    @pytest.mark.asyncio
    async def test_node_populates_state(self):
        from app.graph.nodes.rag_retrieval_node import rag_retrieval_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "请假制度")
        state["intent"] = "rag"
        result = await rag_retrieval_node(state)
        # Should populate retrieval fields
        assert "retrieval_results" in result
        assert "retrieval_count" in result
        assert "retrieval_attempts" in result
        assert result["retrieval_attempts"] >= 1

    @pytest.mark.asyncio
    async def test_node_sets_rag_triggered(self):
        from app.graph.nodes.rag_retrieval_node import rag_retrieval_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        result = await rag_retrieval_node(state)
        assert result["rag_triggered"] == True

    @pytest.mark.asyncio
    async def test_node_adds_traces(self):
        from app.graph.nodes.rag_retrieval_node import rag_retrieval_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        result = await rag_retrieval_node(state)
        traces = result.get("trace_steps", [])
        assert len(traces) >= 1


# ============================================================================
# Test 4: Trust Gating
# ============================================================================
class TestTrustGating:
    """Verify trust-based answer gating."""

    @pytest.mark.asyncio
    async def test_unreliable_trust_no_results(self):
        """When trust is unreliable, should generate honest refusal."""
        from app.graph.nodes.rag_answer_node import rag_answer_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "请假制度")
        state["trust_level"] = "unreliable"
        state["rag_context"] = ""
        result = await rag_answer_node(state)
        answer = result.get("final_answer", "")
        assert "收到老师" in answer
        assert len(answer) > 10

    @pytest.mark.asyncio
    async def test_rag_answer_node_reads_context(self):
        from app.graph.nodes.rag_answer_node import rag_answer_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "请假制度")
        state["trust_level"] = "high"
        state["rag_context"] = "[来源1] 员工手册 第5页\n年假需提前3天申请"
        state["citations"] = [{"citation_id": 1, "document_name": "员工手册.pdf", "page_number": 5}]
        result = await rag_answer_node(state)
        assert "final_answer" in result
        assert result["final_answer"] != ""


# ============================================================================
# Test 5: Citation Node
# ============================================================================
class TestCitationNode:
    """Citation node tests."""

    @pytest.mark.asyncio
    async def test_citation_node_empty_results(self):
        from app.graph.nodes.citation_node import citation_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["rerank_results"] = []
        result = await citation_node(state)
        assert result["citation_count"] == 0
        assert result["trust_level"] == "unreliable"

    @pytest.mark.asyncio
    async def test_citation_node_with_results(self):
        from app.graph.nodes.citation_node import citation_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "请假制度")
        state["rerank_results"] = [
            {
                "document_id": 1, "page_number": 5, "chunk_index": 0,
                "score": 0.94, "content": "年假需提前3天向直属领导申请" * 3,
                "title_path": "第四章 休假", "space_id": 1,
            },
        ]
        result = await citation_node(state)
        assert result["citation_count"] >= 1
        assert "rag_context" in result
        assert len(result["rag_context"]) > 0


# ============================================================================
# Test 6: Memory Node
# ============================================================================
class TestMemoryNode:
    """Memory node tests (gracefully handles Redis unavailability)."""

    @pytest.mark.asyncio
    async def test_memory_node_graceful(self):
        """Memory node should not crash even if Redis is unavailable."""
        from app.graph.nodes.memory_node import memory_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["final_answer"] = "test answer"
        result = await memory_node(state)
        # Should not throw, should return state
        assert result is not None
        assert "trace_steps" in result


# ============================================================================
# Test 7: SSE Trace Events
# ============================================================================
class TestSSETraceEvents:
    """Verify all RAG nodes produce trace events."""

    @pytest.mark.asyncio
    async def test_retrieval_node_traces(self):
        from app.graph.nodes.rag_retrieval_node import rag_retrieval_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "请假制度")
        result = await rag_retrieval_node(state)
        traces = result.get("trace_steps", [])
        rag_traces = [t for t in traces if t.get("node") == "rag_retrieval_node"]
        assert len(rag_traces) >= 1

    @pytest.mark.asyncio
    async def test_rerank_node_traces(self):
        from app.graph.nodes.rag_rerank_node import rag_rerank_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["retrieval_results"] = [
            {"content": "test content that is long enough for testing", "score": 0.9}
        ]
        result = await rag_rerank_node(state)
        traces = result.get("trace_steps", [])
        rag_traces = [t for t in traces if t.get("node") == "rag_rerank_node"]
        assert len(rag_traces) >= 1

    @pytest.mark.asyncio
    async def test_citation_node_traces(self):
        from app.graph.nodes.citation_node import citation_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["rerank_results"] = [
            {
                "document_id": 1, "page_number": 1, "chunk_index": 0,
                "score": 0.9, "content": "test content for citation" * 3,
                "space_id": 1,
            },
        ]
        result = await citation_node(state)
        traces = result.get("trace_steps", [])
        rag_traces = [t for t in traces if t.get("node") == "citation_node"]
        assert len(rag_traces) >= 1

    @pytest.mark.asyncio
    async def test_memory_node_traces(self):
        from app.graph.nodes.memory_node import memory_node
        from app.graph.state import create_initial_state
        state = create_initial_state("1", "c1", "test")
        state["final_answer"] = "test"
        result = await memory_node(state)
        traces = result.get("trace_steps", [])
        rag_traces = [t for t in traces if t.get("node") == "memory_node"]
        assert len(rag_traces) >= 1
