import pytest
from app.graph.nodes.intent_node import (
    _check_clarify_needed,
    _check_info_sufficiency,
    _looks_like_clarify_response,
    _intent_cn,
)


class TestCheckClarifyNeeded:
    def test_intent_clarify_always_returns_true(self):
        assert _check_clarify_needed('clarify', 'any', []) is True

    def test_chat_never_needs_clarify(self):
        assert _check_clarify_needed('chat', 'hello', []) is False

    def test_sql_full_info_no_clarify(self):
        # Has metric, time, and scope keywords
        msg = (
            chr(32479) + chr(35745) + chr(26412) + chr(26376)
            + chr(25216) + chr(26415) + chr(37096)
            + chr(22312) + chr(32844) + chr(20154) + chr(25968)
        )
        assert _check_clarify_needed('sql', msg, []) is False

    def test_sql_missing_all_info_needs_clarify(self):
        msg = chr(26597) + chr(19968) + chr(19979) + chr(25968) + chr(25454)
        assert _check_clarify_needed('sql', msg, []) is True

    def test_sql_after_clarify_no_trigger(self):
        clar = chr(25910) + chr(21040) + chr(32769) + chr(24072) + chr(65374)
        clar += chr(25105) + chr(38656) + chr(35201) + chr(30830) + chr(35748)
        clar += chr(20960) + chr(20010) + chr(20449) + chr(24687)
        history = [{'role': 'assistant', 'content': clar}]
        assert _check_clarify_needed('sql', 'hello', history) is False

    def test_rag_short_message_needs_clarify(self):
        assert _check_clarify_needed('rag', 'x', []) is True

    def test_rag_normal_message_no_clarify(self):
        assert _check_clarify_needed('rag', 'company travel policy for reimbursement process', []) is False


class TestCheckInfoSufficiency:
    def test_returns_tuple(self):
        result = _check_info_sufficiency('chat', 'hello', [])
        assert isinstance(result, tuple)
        assert len(result) == 2
        is_sufficient, missing = result
        assert isinstance(is_sufficient, bool)
        assert isinstance(missing, list)

    def test_sufficient_returns_empty_missing(self):
        is_sufficient, missing = _check_info_sufficiency('chat', 'hello', [])
        assert is_sufficient is True
        assert missing == []

    def test_insufficient_returns_nonempty_missing(self):
        is_sufficient, missing = _check_info_sufficiency('sql', 'help', [])
        assert is_sufficient is False
        assert len(missing) > 0


class TestLooksLikeClarifyResponse:
    def test_detects_clarify_phrases(self):
        clar = chr(25910) + chr(21040) + chr(32769) + chr(24072) + chr(65374)
        clar += chr(25105) + chr(38656) + chr(35201) + chr(30830) + chr(35748)
        clar += chr(20960) + chr(20010) + chr(20449) + chr(24687)
        assert _looks_like_clarify_response(clar) is True

    def test_normal_response_not_clarify(self):
        assert _looks_like_clarify_response('hello') is False
        assert _looks_like_clarify_response('The company has 150 employees') is False


class TestIntentCN:
    def test_known_intents_mapped(self):
        # Verify all known intents return non-empty strings different from intent name
        for intent in ['chat', 'rag', 'sql', 'clarify']:
            result = _intent_cn(intent)
            assert result != intent, f'{intent} should be mapped to a Chinese label'
            assert len(result) > 0
            assert isinstance(result, str)
        # Verify specific mappings by checking they are all different
        results = [_intent_cn(k) for k in ['chat', 'rag', 'sql', 'clarify']]
        assert len(set(results)) == 4, 'all intent labels should be unique'

    def test_unknown_intent_passthrough(self):
        assert _intent_cn('unknown') == 'unknown'
