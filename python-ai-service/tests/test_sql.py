
"""测试 SQL Agent 安全校验。

验证:
  1. SELECT 通过安全校验
  2. DROP/INSERT/UPDATE/DELETE 被拦截
  3. 非 SELECT 开头的语句被拦截
"""

import pytest
from app.sql_agent.security import SQLSecurity


class TestSQLSecurity:
    """测试 SQL 三道防线。"""

    def setup_method(self):
        self.security = SQLSecurity()

    def test_valid_select_passes(self):
        """合法的 SELECT 通过检查。"""
        result = self.security.check("SELECT * FROM employees WHERE status = 'active'")
        assert result["passed"] is True

    def test_select_with_joins_passes(self):
        """带 JOIN 的 SELECT 通过。"""
        result = self.security.check(
            "SELECT e.name, d.name FROM employees e JOIN departments d ON e.dept_id = d.id"
        )
        assert result["passed"] is True

    def test_select_with_cte_passes(self):
        """WITH CTE 的 SELECT 通过。"""
        result = self.security.check(
            "WITH active AS (SELECT * FROM employees WHERE status='active') SELECT COUNT(*) FROM active"
        )
        assert result["passed"] is True

    def test_drop_blocked(self):
        """DROP 被拦截。"""
        result = self.security.check("DROP TABLE employees")
        assert result["passed"] is False
        assert "DROP" in result["reason"]

    def test_insert_blocked(self):
        """INSERT 被拦截。"""
        result = self.security.check("INSERT INTO employees VALUES (1, 'test')")
        assert result["passed"] is False

    def test_update_blocked(self):
        """UPDATE 被拦截。"""
        result = self.security.check("UPDATE employees SET status = 'resigned'")
        assert result["passed"] is False

    def test_delete_blocked(self):
        """DELETE 被拦截。"""
        result = self.security.check("DELETE FROM employees WHERE id = 1")
        assert result["passed"] is False

    def test_alter_blocked(self):
        """ALTER 被拦截。"""
        result = self.security.check("ALTER TABLE employees ADD COLUMN age INT")
        assert result["passed"] is False

    def test_non_select_statement_blocked(self):
        """非查询语句被拦截。"""
        result = self.security.check("SET @var = 1")
        assert result["passed"] is False

    def test_show_tables_passes(self):
        """SHOW 语句通过。"""
        result = self.security.check("SHOW TABLES")
        assert result["passed"] is True

    def test_describe_passes(self):
        """DESCRIBE 通过。"""
        result = self.security.check("DESCRIBE employees")
        assert result["passed"] is True

    def test_explain_passes(self):
        """EXPLAIN 通过。"""
        result = self.security.check("EXPLAIN SELECT * FROM employees")
        assert result["passed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
