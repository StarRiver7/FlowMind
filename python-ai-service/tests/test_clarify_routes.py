import pytest
from app.graph.state import create_initial_state
from app.graph.edges.routes import route_after_intent, route_after_slot_collect

class TestRouteAfterIntent:
    def test_normal_chat_routes_to_router(self):
        state = create_initial_state("u1", "c1", "hello")
        assert route_after_intent(state) == "router_node"

    def test_clarify_required_routes_to_clarify(self):
        state = create_initial_state("u1", "c1", "stats")
        state["clarify_required"] = True
        assert route_after_intent(state) == "clarify_node"

    def test_clarify_pending_routes_to_slot_collect(self):
        state = create_initial_state("u1", "c1", "tech dept")
        state["clarify_pending"] = True
        assert route_after_intent(state) == "slot_collect_node"

    def test_clarify_pending_takes_priority_over_required(self):
        state = create_initial_state("u1", "c1", "ans")
        state["clarify_pending"] = True
        state["clarify_required"] = True
        assert route_after_intent(state) == "slot_collect_node"

class TestRouteAfterSlotCollect:
    def test_finished_routes_to_task_resume(self):
        state = create_initial_state("u1", "c1", "ans")
        state["clarify_finished"] = True
        assert route_after_slot_collect(state) == "task_resume_node"

    def test_not_finished_routes_to_clarify(self):
        state = create_initial_state("u1", "c1", "ans")
        state["clarify_finished"] = False
        state["missing_slots"] = ["time_range"]
        assert route_after_slot_collect(state) == "clarify_node"
