import pytest
from app.graph.clarify.slot_manager import SlotManager, SLOT_SCHEMAS

class TestSlotSchemas:
    def test_sql_schema_has_required_slots(self):
        slots = SLOT_SCHEMAS["sql_query"]
        names = [s["name"] for s in slots]
        assert "department" in names
        assert "time_range" in names
        assert "metric" in names
        assert len(slots) >= 3

    def test_rag_schema_has_required_slots(self):
        slots = SLOT_SCHEMAS["rag_query"]
        names = [s["name"] for s in slots]
        assert "topic" in names

    def test_all_slots_have_name_and_label(self):
        for intent, slots in SLOT_SCHEMAS.items():
            for s in slots:
                assert "name" in s
                assert "label" in s

class TestSlotCheckMissing:
    def test_all_missing_when_empty_collected(self):
        slots = SLOT_SCHEMAS["sql_query"]
        missing = SlotManager.check_missing(slots, {})
        assert len(missing) == 3  # department, time_range, metric

    def test_none_missing_when_all_collected(self):
        slots = SLOT_SCHEMAS["sql_query"]
        collected = {"department": "tech", "time_range": "this month", "metric": "headcount"}
        missing = SlotManager.check_missing(slots, collected)
        assert len(missing) == 0

    def test_optional_slots_not_checked(self):
        slots = SLOT_SCHEMAS["sql_query"]
        collected = {"department": "tech", "time_range": "m", "metric": "h"}
        missing = SlotManager.check_missing(slots, collected)
        assert "include_inactive" not in missing  # optional

    def test_partial_collected(self):
        slots = SLOT_SCHEMAS["sql_query"]
        collected = {"department": "tech"}
        missing = SlotManager.check_missing(slots, collected)
        assert "time_range" in missing
        assert "metric" in missing
        assert "department" not in missing

class TestSlotGetInfo:
    def test_get_existing_slot(self):
        slots = SLOT_SCHEMAS["sql_query"]
        info = SlotManager.get_slot_info("department", slots)
        assert info is not None
        assert info["name"] == "department"

    def test_get_nonexistent_slot(self):
        slots = SLOT_SCHEMAS["sql_query"]
        info = SlotManager.get_slot_info("nonexistent", slots)
        assert info is None

class TestSlotGetSlots:
    def test_get_sql_slots(self):
        slots = SlotManager.get_slots("sql_query")
        assert len(slots) >= 3

    def test_unknown_intent_returns_empty(self):
        slots = SlotManager.get_slots("unknown")
        assert slots == []
