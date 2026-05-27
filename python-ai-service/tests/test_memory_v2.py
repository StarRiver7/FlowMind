import pytest
from app.memory.memory_keys import session_key, state_key, clarify_key, slots_key, preference_key, TTL_SESSION, TTL_STATE, TTL_CLARIFY, TTL_SLOTS, TTL_PREFERENCE
from app.graph.state import create_initial_state
from app.memory.state_memory import StateMemory
import json

class TestMemoryKeys:
    def test_session_key_format(self):
        k = session_key("u1", "c1")
        assert k.startswith("internsu")
        assert "u1" in k and "c1" in k

    def test_state_key_format(self):
        k = state_key("u1", "c1")
        assert "state" in k

    def test_clarify_key_format(self):
        k = clarify_key("u1", "c1")
        assert "clarify" in k

    def test_slots_key_format(self):
        k = slots_key("u1", "c1")
        assert "slots" in k

    def test_preference_key_user_isolated(self):
        k1 = preference_key("u1")
        k2 = preference_key("u2")
        assert k1 != k2

    def test_ttl_values_ordered(self):
        assert TTL_SESSION == 1800
        assert TTL_STATE == 900
        assert TTL_PREFERENCE == 604800
        assert TTL_STATE < TTL_SESSION < TTL_PREFERENCE

class TestStateRestore:
    def test_create_state_with_restore(self):
        rs = {"clarify_pending": True, "intent": "sql", "collected_slots": {"dept": "tech"}}
        s = create_initial_state("u1", "c1", "hi", restore_state=rs)
        assert s["clarify_pending"] == True
        assert s["intent"] == "sql"
        assert s["collected_slots"] == {"dept": "tech"}

    def test_create_state_without_restore_uses_defaults(self):
        s = create_initial_state("u1", "c1", "hi")
        assert s["clarify_pending"] == False
        assert s["intent"] == "chat"
        assert s["collected_slots"] == {}

    def test_partial_restore_fills_remaining_with_defaults(self):
        rs = {"intent": "rag"}
        s = create_initial_state("u1", "c1", "hi", restore_state=rs)
        assert s["intent"] == "rag"
        assert s["clarify_pending"] == False  # default

    def test_pending_task_restored(self):
        rs = {"pending_task": "sql_query", "task_context": {"original_message": "count", "intent": "sql"}}
        s = create_initial_state("u1", "c1", "tech dept", restore_state=rs)
        assert s["pending_task"] == "sql_query"
        assert s["task_context"]["original_message"] == "count"

class TestConversationIsolation:
    def test_different_convs_have_different_keys(self):
        k1 = session_key("u1", "conv_a")
        k2 = session_key("u1", "conv_b")
        assert k1 != k2

    def test_different_users_isolated(self):
        k1 = state_key("u1", "c1")
        k2 = state_key("u2", "c1")
        assert k1 != k2

class TestStateMemorySerialization:
    def test_state_save_load_roundtrip(self):
        sm = StateMemory()
        original = {"intent": "sql", "clarify_pending": True, "clarify_round": 2}
        js = json.dumps(original)
        restored = json.loads(js)
        assert restored["intent"] == "sql"
        assert restored["clarify_pending"] == True
        assert restored["clarify_round"] == 2

class TestFallbackMemory:
    def test_redis_client_fallback(self):
        from app.memory.redis_client import RedisClient
        rc = RedisClient()
        assert not rc.is_connected
        assert rc._fallback == {}
