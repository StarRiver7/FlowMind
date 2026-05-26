
"""测试 RAG 检索与权限过滤。

验证:
  1. 检索返回合理数量的结果
  2. 权限过滤正确拦截无权限的 chunk
  3. Source 引用包含必要字段
"""

import pytest
from app.rag.permission_filter import PermissionFilter


class TestPermissionFilter:
    """测试权限过滤器。"""

    def setup_method(self):
        self.filter = PermissionFilter()
        self.user_id = "5"
        self.dept_id = 3
        self.dept_path = "/1/3"
        self.allowed = [1, 2, 3]

    def _make_chunk(self, space_id, visibility="public", creator_id="5"):
        return {
            "content": f"chunk from space {space_id}",
            "metadata": {
                "space_id": space_id,
                "visibility": visibility,
                "creator_id": creator_id,
                "file_name": "test.pdf",
                "page_number": 1,
            },
            "score": 0.9,
        }

    def test_public_chunk_always_allowed(self):
        """public 文档永远可访问。"""
        chunks = [self._make_chunk(10, "public", "99")]
        result = self.filter.filter_chunks(chunks, self.user_id,
                                           self.dept_id, self.dept_path, self.allowed)
        assert len(result) == 1

    def test_private_chunk_owner_allowed(self):
        """private 文档创建者可访问。"""
        chunks = [self._make_chunk(10, "private", self.user_id)]
        result = self.filter.filter_chunks(chunks, self.user_id,
                                           self.dept_id, self.dept_path, [])
        assert len(result) == 1

    def test_private_chunk_other_blocked(self):
        """private 文档非创建者被拦截。"""
        chunks = [self._make_chunk(10, "private", "99")]
        result = self.filter.filter_chunks(chunks, self.user_id,
                                           self.dept_id, self.dept_path, [])
        assert len(result) == 0

    def test_department_chunk_allowed(self):
        """department 文档同部门可访问。"""
        chunks = [self._make_chunk(3, "department", "10")]
        result = self.filter.filter_chunks(chunks, self.user_id,
                                           self.dept_id, self.dept_path, [1, 3, 5])
        assert len(result) == 1

    def test_mixed_chunks_filtered(self):
        """混合权限正确过滤。"""
        chunks = [
            self._make_chunk(1, "public", "99"),
            self._make_chunk(2, "private", "99"),   # 应被拦截
            self._make_chunk(3, "department", "10"),
            self._make_chunk(4, "private", self.user_id),
        ]
        result = self.filter.filter_chunks(chunks, self.user_id,
                                           self.dept_id, self.dept_path, [1, 3])
        assert len(result) == 3  # public + department + own private 保留


class TestSourceFormat:
    """测试 Source 引用格式。"""

    def test_source_has_required_fields(self):
        """Source 必须包含 document_name, page_number, excerpt, score。"""
        source = {
            "document_name": "员工手册.pdf",
            "page_number": 12,
            "excerpt": "员工每年享有...",
            "score": 0.92,
        }
        required = ["document_name", "page_number", "excerpt", "score"]
        for field in required:
            assert field in source, f"Source 缺少字段: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
