import pytest
from app.llm.prompt_builder import PromptBuilder


class TestPromptBuilder:
    def setup_method(self):
        self.builder = PromptBuilder()

    def test_build_basic_messages(self):
        messages = self.builder.build("Hello")
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "Hello"

    def test_build_with_history(self):
        history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello there"}]
        messages = self.builder.build("What is AI?", history=history)
        assert len(messages) == 4  # system + 2 history + user
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hi"

    def test_build_rag_prompt(self):
        docs = [{"source": "doc1.pdf", "content": "AI stands for Artificial Intelligence."}]
        messages = self.builder.build_rag_prompt("What is AI?", docs)
        assert len(messages) >= 2
        system = messages[0]["content"]
        assert "AI stands for Artificial Intelligence" in system
        assert "doc1.pdf" in system

    def test_build_sql_prompt(self):
        schema = "CREATE TABLE users (id INT, name VARCHAR);"
        messages = self.builder.build_sql_prompt("Show all users", schema)
        system = messages[0]["content"]
        assert "CREATE TABLE" in system
        assert messages[-1]["content"] == "Show all users"
