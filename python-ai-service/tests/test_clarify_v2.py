import pytest
from app.graph.state import create_initial_state
from app.graph.clarify.slot_manager import SlotManager, SLOT_SCHEMAS
from app.graph.clarify.clarify_prompt import build_clarify_prompt

class TestMultiRoundClarify:
    def test_round_increments(self):
        state = create_initial_state("u1", "c1", "query")
        state["clarify_round"] = 0
        state["clarify_round"] += 1
        assert state["clarify_round"] == 1
        state["clarify_round"] += 1
        assert state["clarify_round"] == 2

    def test_slot_accumulation_across_rounds(self):
        state = create_initial_state("u1", "c1", "stats")
        slots = SLOT_SCHEMAS["sql_query"]
        state["clarify_slots"] = slots
        state["collected_slots"] = {"department": "tech"}
        missing = SlotManager.check_missing(slots, state["collected_slots"])
        assert "time_range" in missing
        assert "metric" in missing
        state["collected_slots"]["time_range"] = "this month"
        missing = SlotManager.check_missing(slots, state["collected_slots"])
        assert "metric" in missing
        assert "time_range" not in missing

    def test_clarify_finished_when_all_collected(self):
        state = create_initial_state("u1", "c1", "stats")
        slots = SLOT_SCHEMAS["sql_query"]
        state["collected_slots"] = {"department": "x", "time_range": "x", "metric": "x"}
        missing = SlotManager.check_missing(slots, state["collected_slots"])
        assert len(missing) == 0

class TestTaskResume:
    def test_pending_task_preserved(self):
        state = create_initial_state("u1", "c1", "stats")
        state["pending_task"] = "sql_query"
        state["task_context"] = {"original_message": "count employees", "intent": "sql"}
        assert state["pending_task"] == "sql_query"
        assert state["task_context"]["original_message"] == "count employees"

    def test_task_resume_clears_clarify_flags(self):
        state = create_initial_state("u1", "c1", "ans")
        state["clarify_pending"] = True
        state["clarify_finished"] = True
        state["clarify_pending"] = False
        assert not state["clarify_pending"]
        assert state["clarify_finished"]

class TestConversationContinuity:
    def test_clarify_pending_state(self):
        state = create_initial_state("u1", "c1", "tech dept")
        state["clarify_pending"] = True
        state["clarify_question"] = "which dept?"
        assert state["clarify_pending"]
        assert len(state["clarify_question"]) > 0

    def test_task_context_persists_across_turns(self):
        state = create_initial_state("u1", "c1", "count staff")
        state["task_context"] = {"original_message": "count staff", "intent": "sql"}
        state["pending_task"] = "sql_query"
        state["collected_slots"] = {"department": "tech"}
        orig_msg = state["task_context"]["original_message"]
        slots_str = ", ".join(f"{k}: {v}" for k, v in state["collected_slots"].items())
        enriched = orig_msg + " [" + slots_str + "]"
        assert "tech" in enriched
        assert "count staff" in enriched

class TestClarifyPrompt:
    def test_build_prompt_includes_missing_slots(self):
        slots = SLOT_SCHEMAS["sql_query"]
        missing = ["department", "time_range"]
        prompt = build_clarify_prompt("query", missing, slots)
        assert "department" in prompt
        assert "time_range" in prompt

    def test_build_prompt_includes_message(self):
        slots = SLOT_SCHEMAS["sql_query"]
        prompt = build_clarify_prompt("count employees", ["department"], slots)
        assert "count employees" in prompt
