"""InternSU SQL Agent - Natural language to SQL.

Modules:
  generator:    NL2SQL generation
  security:     SQL 3-line defense security check
  sql_guard:    Alias for security module
  executor:     SQL read-only execution
  schema_loader: Auto-read MySQL schema, build Schema Context
  schema_cache:  TTL-based schema cache
  sql_prompt:    InternSU personality prompt templates for SQL
  sql_summarizer: LLM summarizes query results in natural language
  sql_trace:     Structured trace steps for SSE
  sql_memory:    SQL context reuse via Redis
"""

from app.sql_agent.generator import sql_generator, SQLGenerator
from app.sql_agent.security import sql_security, SQLSecurity
from app.sql_agent.sql_guard import DANGEROUS_KEYWORDS, ALLOWED_KEYWORDS
from app.sql_agent.executor import sql_executor, SQLExecutor
from app.sql_agent.schema_loader import schema_loader, SchemaLoader
from app.sql_agent.schema_cache import schema_cache, SchemaCache
from app.sql_agent.sql_prompt import (
    SQL_GENERATE_SYSTEM, SQL_GENERATE_USER,
    SQL_SUMMARIZE_SYSTEM, SQL_SUMMARIZE_USER,
)
from app.sql_agent.sql_summarizer import sql_summarizer, SQLSummarizer
from app.sql_agent.sql_trace import trace_step, SQL_TRACE_MESSAGES
from app.sql_agent.sql_memory import sql_memory_helper, SQLMemory

__all__ = [
    "sql_generator", "SQLGenerator",
    "sql_security", "SQLSecurity",
    "DANGEROUS_KEYWORDS", "ALLOWED_KEYWORDS",
    "sql_executor", "SQLExecutor",
    "schema_loader", "SchemaLoader",
    "schema_cache", "SchemaCache",
    "SQL_GENERATE_SYSTEM", "SQL_GENERATE_USER",
    "SQL_SUMMARIZE_SYSTEM", "SQL_SUMMARIZE_USER",
    "sql_summarizer", "SQLSummarizer",
    "trace_step", "SQL_TRACE_MESSAGES",
    "sql_memory_helper", "SQLMemory",
]
