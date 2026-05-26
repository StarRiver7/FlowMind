"""
SQL Guard — 用户指定的入口文件。

本模块是 sql_agent/security.py 的便捷别名。
"""

from app.sql_agent.security import SQLSecurity, sql_security, DANGEROUS_KEYWORDS, ALLOWED_KEYWORDS

__all__ = ["SQLSecurity", "sql_security", "DANGEROUS_KEYWORDS", "ALLOWED_KEYWORDS"]
