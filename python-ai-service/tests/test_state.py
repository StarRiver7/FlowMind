"""Test InternState creation and typing."""
import pytest
from app.graph.state import InternState, create_initial_state


class TestStateCreation:
    """Test state initialization."""

    def test_create_initial_state_defaults(self):
        """Verify all fields are initialized with correct defaults."""
        state = create_initial_state(
            user_id="u1",
            conversation_id="c1",
            message="hello",
        )
        assert state["user_id"] == "u1"
        assert state["conversation_id"] == "c1"
        assert state["user_message"] == "hello"
        assert state["intent"] == "chat"
        assert state["intent_confidence"] == 0.0
        assert state["clarify_required"] is False
        assert state["clarify_question"] == ""
        assert state["clarify_round"] == 0
        assert state["clarify_pending"] is False
        assert state["collected_slots"] == {}
        assert state["current_node"] == ""
        assert state["next_node"] == ""
        assert state["trace_steps"] == []
        assert state["sources"] == []
        assert state["final_answer"] == ""
        assert state["tokens_used"] == 0
        assert state["model_name"] == "deepseek-chat"
        assert state["error"] is None
        assert state["done"] is False

    def test_create_with_history(self):
        """Verify history is passed through."""
        history = [{"role": "user", "content": "hi"}]
        state = create_initial_state("u1", "c1", "hello", history=history)
        assert state["conversation_context"] == history

    def test_create_with_custom_model(self):
        """Verify custom model name."""
        state = create_initial_state("u1", "c1", "hello", model_name="gpt-4")
        assert state["model_name"] == "gpt-4"

    def test_state_is_typed_dict(self):
        """Verify state is a dict-like object."""
        state = create_initial_state("u1", "c1", "hello")
        assert isinstance(state, dict)
        assert "user_id" in state


class TestStateMutation:
    """Test state mutation patterns used by graph nodes."""

    def test_trace_steps_append(self):
        """Verify trace_steps can be appended."""
        state = create_initial_state("u1", "c1", "hello")
        state["trace_steps"] = state["trace_steps"] + [{
            "node": "intent_node",
            "message": "testing",
            "status": "running",
        }]
        assert len(state["trace_steps"]) == 1
        assert state["trace_steps"][0]["node"] == "intent_node"

    def test_intent_update(self):
        """Verify intent can be updated."""
        state = create_initial_state("u1", "c1", "stats")
        state["intent"] = "sql"
        state["intent_confidence"] = 0.95
        assert state["intent"] == "sql"
        assert state["intent_confidence"] == 0.95

    def test_clarify_state_transition(self):
        """Verify clarify state machine transitions."""
        state = create_initial_state("u1", "c1", "stats")
        # Simulate clarify flow
        state["clarify_required"] = True
        state["clarify_round"] = 1
        state["clarify_pending"] = True
        state["clarify_question"] = "receive teacher~ need confirm?"
        state["final_answer"] = state["clarify_question"]
        state["done"] = True

        assert state["clarify_pending"] is True
        assert state["done"] is True
        assert "receive teacher" in state["final_answer"]

    def test_answer_flow(self):
        """Verify normal answer flow."""
        state = create_initial_state("u1", "c1", "hello")
        state["intent"] = "chat"
        state["final_answer"] = "hello teacher~"
        state["done"] = True
        assert state["done"] is True
        assert state["clarify_pending"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
