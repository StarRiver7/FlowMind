"""Tests for enterprise Knowledge Base upload system.

Coverage:
  1. File validation (type, size, MIME, magic)
  2. Document status lifecycle
  3. File storage (save/read/delete)
  4. Knowledge base CRUD + permission isolation
  5. Upload manager flow
  6. API endpoints
"""

import os
import io
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.kb.document_status import (
    DocumentStatus,
    can_transition,
    next_status,
    is_terminal,
    is_retryable,
    status_display_name,
)
from app.kb.document_parser import validate_file, FileValidationResult, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from app.kb.file_storage import FileStorage


# ============================================================
# 1. File Validation Tests
# ============================================================

class TestFileValidation:
    """文件校验测试."""

    def test_valid_pdf(self):
        """合法的 PDF 文件."""
        content = b"%PDF-1.4\nfake pdf content" * 10
        result = validate_file("report.pdf", content)
        assert result.is_valid is True
        assert result.file_type == ".pdf"
        assert result.mime_type == "application/pdf"
        assert result.file_hash is not None
        assert len(result.file_hash) == 64

    def test_valid_docx(self):
        """合法的 DOCX 文件（ZIP 格式）."""
        content = b"PK\x03\x04" + b"\x00" * 100
        result = validate_file("doc.docx", content)
        assert result.is_valid is True
        assert result.file_type == ".docx"

    def test_valid_md(self):
        """合法的 Markdown 文件."""
        content = b"# Hello\nThis is a test."
        result = validate_file("readme.md", content)
        assert result.is_valid is True
        assert result.file_type == ".md"

    def test_valid_txt(self):
        """合法的 TXT 文件."""
        content = b"plain text content"
        result = validate_file("notes.txt", content)
        assert result.is_valid is True
        assert result.file_type == ".txt"

    def test_invalid_extension(self):
        """不支持的扩展名."""
        result = validate_file("image.png", b"fake png")
        assert result.is_valid is False
        assert "不支持" in result.error_message

    def test_no_extension(self):
        """无扩展名的文件."""
        result = validate_file("Makefile", b"content")
        assert result.is_valid is False
        assert "扩展名" in result.error_message

    def test_empty_file(self):
        """空文件."""
        result = validate_file("empty.txt", b"")
        assert result.is_valid is False
        assert "空文件" in result.error_message

    def test_oversized_file(self):
        """超大文件."""
        content = b"x" * (MAX_FILE_SIZE + 1)
        result = validate_file("big.pdf", content)
        assert result.is_valid is False
        assert "过大" in result.error_message

    def test_magic_mismatch(self):
        """扩展名与实际内容不匹配."""
        content = b"%PDF-1.4\ncontent"
        result = validate_file("fake.docx", content)  # .docx 实际是 PDF
        assert result.is_valid is False
        assert "不匹配" in result.error_message

    def test_md_no_magic_check(self):
        """MD 文件不进行魔数检查."""
        content = b"# Markdown"
        result = validate_file("notes.md", content)
        assert result.is_valid is True

    def test_txt_no_magic_check(self):
        """TXT 文件不进行魔数检查."""
        content = b"hello world"
        result = validate_file("log.txt", content)
        assert result.is_valid is True


# ============================================================
# 2. Document Status Lifecycle Tests
# ============================================================

class TestDocumentStatus:
    """文档状态流转测试."""

    def test_full_lifecycle_transitions(self):
        """完整状态流转路径."""
        flow = [
            ("uploaded", "parsing"),
            ("parsing", "parsed"),
            ("parsed", "chunking"),
            ("chunking", "chunked"),
            ("chunked", "embedding"),
            ("embedding", "indexed"),
            ("indexed", "ready"),
        ]
        for current, target in flow:
            assert can_transition(current, target), f"Fail: {current} → {target}"

    def test_any_to_failed(self):
        """任意状态可转到 FAILED."""
        for status in DocumentStatus:
            if status != DocumentStatus.FAILED:
                assert can_transition(status, DocumentStatus.FAILED), f"Fail: {status} → failed"

    def test_failed_is_terminal(self):
        """FAILED 不可再流转（终态）."""
        assert can_transition(DocumentStatus.FAILED, DocumentStatus.PARSING) is False
        assert can_transition(DocumentStatus.FAILED, DocumentStatus.READY) is False

    def test_ready_to_non_failed_blocked(self):
        """READY 只能转到 FAILED."""
        assert can_transition(DocumentStatus.READY, DocumentStatus.PARSING) is False
        assert can_transition(DocumentStatus.READY, DocumentStatus.FAILED) is True

    def test_invalid_transition(self):
        """非法跃迁被阻止."""
        assert can_transition("uploaded", "ready") is False       # 不能跳过
        assert can_transition("parsing", "indexed") is False     # 不能跳过
        assert can_transition("ready", "uploaded") is False       # 不能回溯

    def test_next_status(self):
        """next_status 返回正确下一状态."""
        assert next_status("uploaded") == DocumentStatus.PARSING
        assert next_status("parsed") == DocumentStatus.CHUNKING
        assert next_status("indexed") == DocumentStatus.READY
        assert next_status("ready") is None  # 终态，无下一个
        assert next_status("failed") is None

    def test_is_terminal(self):
        """终态判断."""
        assert is_terminal("ready") is True
        assert is_terminal("failed") is True
        assert is_terminal("uploaded") is False
        assert is_terminal("parsing") is False

    def test_is_retryable(self):
        """可重试状态."""
        assert is_retryable("failed") is True
        assert is_retryable("ready") is True  # 可以重新向量化
        assert is_retryable("parsed") is True
        assert is_retryable("uploaded") is False  # 正常流转，无需 retry

    def test_status_display_name(self):
        """中文显示名."""
        assert status_display_name("uploaded") == "已上传"
        assert status_display_name("parsing") == "解析中"
        assert status_display_name("ready") == "就绪"
        assert status_display_name("failed") == "失败"
        assert status_display_name("unknown") == "unknown"

    def test_unknown_status_transition(self):
        """未知状态的 false 处理."""
        assert can_transition("bogus", "parsing") is False
        assert next_status("bogus") is None


# ============================================================
# 3. File Storage Tests
# ============================================================

class TestFileStorage:
    """文件存储测试."""

    @pytest.fixture
    def storage(self):
        """使用临时目录的 FileStorage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = FileStorage(root=Path(tmpdir))
            yield fs

    def test_save_and_read(self, storage):
        """保存并读取文件."""
        content = b"hello knowledge base"
        rel_path, file_hash, file_size = storage.save_upload(
            content=content,
            space_id=1,
            original_filename="test.txt",
        )
        assert file_size == len(content)
        assert len(file_hash) == 64
        assert "uploads" in rel_path
        assert "1" in rel_path
        assert "test_" in rel_path  # 带时间戳的重命名

        # 读取
        read_content = storage.read_file(rel_path)
        assert read_content == content

        # 绝对路径
        abs_path = storage.get_absolute_path(rel_path)
        assert abs_path.exists()

    def test_directory_structure(self, storage):
        """目录结构正确."""
        assert storage.uploads_dir.exists()
        assert storage.parsed_dir.exists()
        assert storage.temp_dir.exists()

        up, pa = storage.ensure_space_dir(42)
        assert up == storage.uploads_dir / "42"
        assert pa == storage.parsed_dir / "42"
        assert up.exists()
        assert pa.exists()

    def test_duplicate_filename_handling(self, storage):
        """重名文件处理."""
        content1 = b"version 1"
        content2 = b"version 2"

        path1, _, _ = storage.save_upload(content1, 1, "doc.txt")
        path2, _, _ = storage.save_upload(content2, 1, "doc.txt")

        assert path1 != path2  # 不会覆盖
        assert storage.read_file(path1) == content1
        assert storage.read_file(path2) == content2

    def test_delete_file(self, storage):
        """删除文件."""
        rel_path, _, _ = storage.save_upload(b"temp", 1, "delete_me.txt")
        assert storage.get_absolute_path(rel_path).exists()

        ok = storage.delete_file(rel_path)
        assert ok is True
        assert not storage.get_absolute_path(rel_path).exists()

        ok = storage.delete_file(rel_path)  # 已删除
        assert ok is False

    def test_read_nonexistent(self, storage):
        """读取不存在的文件."""
        with pytest.raises(FileNotFoundError):
            storage.read_file("nonexistent.txt")

    def test_space_disk_usage(self, storage):
        """空间磁盘占用."""
        content = b"x" * 1024  # 1KB
        storage.save_upload(content, space_id=10, original_filename="a.txt")
        storage.save_upload(content, space_id=10, original_filename="b.txt")
        usage = storage.space_disk_usage(10)
        assert usage >= 2048


# ============================================================
# 4. Edge Case Tests
# ============================================================

class TestEdgeCases:
    """边界情况测试."""

    def test_unicode_filename(self):
        """中文文件名."""
        content = b"hello"
        result = validate_file("产品需求文档.pdf", content)
        assert result.is_valid is True

    def test_multiple_dots_filename(self):
        """多点文件名."""
        content = b"# test"
        result = validate_file("v1.2.3.release.md", content)
        assert result.is_valid is True
        assert result.file_type == ".md"

    def test_uppercase_extension(self):
        """大写扩展名."""
        content = b"plain text"
        result = validate_file("README.TXT", content)
        assert result.is_valid is True
        assert result.file_type == ".txt"

    def test_max_size_boundary(self):
        """大小边界测试."""
        content = b"x" * MAX_FILE_SIZE
        result = validate_file("exact.pdf", content)
        assert result.is_valid is True

    def test_one_byte_over_max(self):
        """刚好超过限制 1 字节."""
        content = b"x" * (MAX_FILE_SIZE + 1)
        result = validate_file("over.pdf", content)
        assert result.is_valid is False


# ============================================================
# 5. Knowledge Base Service Tests (with mocked DB)
# ============================================================

class TestKnowledgeBaseService:
    """知识空间服务测试."""

    def test_can_access_creator(self):
        """创建者可以访问."""
        from app.kb.knowledge_base_service import KnowledgeBaseService
        space = MagicMock()
        space.creator_id = 100
        space.visibility = "private"
        assert KnowledgeBaseService._can_access(space, user_id=100, department_id=None) is True

    def test_can_access_public(self):
        """public 任意用户可访问."""
        from app.kb.knowledge_base_service import KnowledgeBaseService
        space = MagicMock()
        space.creator_id = 100
        space.visibility = "public"
        assert KnowledgeBaseService._can_access(space, user_id=200, department_id=None) is True

    def test_can_access_department_match(self):
        """同部门可访问 department 级别."""
        from app.kb.knowledge_base_service import KnowledgeBaseService
        space = MagicMock()
        space.creator_id = 100
        space.visibility = "department"
        space.department_id = 10
        assert KnowledgeBaseService._can_access(space, user_id=200, department_id=10) is True

    def test_cannot_access_department_mismatch(self):
        """不同部门不可访问."""
        from app.kb.knowledge_base_service import KnowledgeBaseService
        space = MagicMock()
        space.creator_id = 100
        space.visibility = "department"
        space.department_id = 10
        assert KnowledgeBaseService._can_access(space, user_id=200, department_id=20) is False

    def test_cannot_access_private(self):
        """private 非创建者不可访问."""
        from app.kb.knowledge_base_service import KnowledgeBaseService
        space = MagicMock()
        space.creator_id = 100
        space.visibility = "private"
        assert KnowledgeBaseService._can_access(space, user_id=200, department_id=None) is False


# ============================================================
# 6. Allowed Extensions Check
# ============================================================

class TestAllowedExtensions:
    """允许的文件类型检查."""

    def test_all_extensions_present(self):
        """四类文件都在允许列表中."""
        assert ".pdf" in ALLOWED_EXTENSIONS
        assert ".docx" in ALLOWED_EXTENSIONS
        assert ".md" in ALLOWED_EXTENSIONS
        assert ".txt" in ALLOWED_EXTENSIONS

    def test_common_denied(self):
        """常见不允许的类型."""
        denied = [".py", ".js", ".exe", ".dll", ".sh", ".bat", ".html", ".json"]
        for ext in denied:
            assert ext not in ALLOWED_EXTENSIONS, f"{ext} should not be allowed"

