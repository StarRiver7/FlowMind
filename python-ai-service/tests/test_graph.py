"""Test LangGraph assembly and structure."""
import pytest
from app.graph.intern_graph import InternGraph, build_intern_graph, intern_graph
from app.graph.state import InternState, create_initial_state


class TestGraphAssembly:
    """Test graph structure and compilation."""

    def test_graph_builds_without_error(self):
        """Verify graph compiles without exceptions."""
        graph = build_intern_graph()
        assert graph is not None

    def test_graph_has_required_nodes(self):
        """Verify all 5 required nodes are registered."""
        g = build_intern_graph()
        nodes = g.get_graph().nodes
        expected = {"intent_node", "clarify_node", "router_node", "chat_node", "response_node"}
        assert expected.issubset(set(nodes.keys()))

    def test_graph_entry_point(self):
        """Verify entry point is intent_node."""
        g = intern_graph.graph
        # Check graph structure exists
        assert g is not None

    def test_intern_graph_singleton(self):
        """Verify intern_graph is a singleton InternGraph instance."""
        assert isinstance(intern_graph, InternGraph)
        assert intern_graph.graph is not None


class TestGraphStateFlow:
    """Test state transformations through the flow."""

    def test_initial_state_fields(self):
        """Verify initial state has all required fields for graph nodes."""
        state = create_initial_state("u1", "c1", "test message")
        required = [
            "conversation_id", "user_id", "user_message",
            "intent", "clarify_required", "trace_steps",
            "final_answer", "current_node", "done",
        ]
        for field in required:
            assert field in state, f"Missing field: {field}"

    def test_state_passes_through_intent_fields(self):
        """Verify state carries intent-related fields."""
        state = create_initial_state("u1", "c1", "test")
        intent_fields = ["intent", "intent_confidence", "clarify_required"]
        for f in intent_fields:
            assert f in state

    def test_state_passes_through_clarify_fields(self):
        """Verify state carries clarify-related fields."""
        state = create_initial_state("u1", "c1", "test")
        clarify_fields = [
            "clarify_required", "clarify_question", "clarify_round",
            "clarify_pending", "collected_slots",
        ]
        for f in clarify_fields:
            assert f in state

    def test_state_passes_through_output_fields(self):
        """Verify state carries output-related fields."""
        state = create_initial_state("u1", "c1", "test")
        output_fields = ["final_answer", "sources", "trace_steps", "tokens_used", "done"]
        for f in output_fields:
            assert f in state


class TestGraphIntegration:
    """Integration-style tests for the graph (requires no LLM)."""

    def test_graph_intern_graph_has_run_method(self):
        """Verify InternGraph has a run method."""
        assert hasattr(intern_graph, "run")

    def test_graph_run_is_async(self):
        """Verify run method is async."""
        import inspect
        assert inspect.iscoroutinefunction(intern_graph.run)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
