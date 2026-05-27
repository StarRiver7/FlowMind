"""Document parser — 文件类型校验 / MIME检测 / 基础元信息提取.

本阶段仅做校验和元数据提取，不实现正文解析（正文解析留给下一阶段 RAG Pipeline）。
"""

import hashlib
import os
from typing import Optional
from dataclasses import dataclass


# 支持的文件类型及其 MIME 映射
ALLOWED_EXTENSIONS = frozenset({".pdf", ".docx", ".md", ".txt"})

MIME_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".md": "text/markdown",
    ".txt": "text/plain",
}

# 文件大小上限: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024

# 魔数签名检测 (用于绕过扩展名伪造)
MAGIC_SIGNATURES = {
    b"%PDF": ".pdf",
    b"PK\x03\x04": ".docx",  # DOCX 实际是 ZIP 格式
}


@dataclass
class FileValidationResult:
    """文件校验结果."""
    is_valid: bool
    file_type: Optional[str] = None       # 检测到的文件类型扩展名，如 ".pdf"
    mime_type: Optional[str] = None
    file_size: int = 0
    error_message: Optional[str] = None
    file_hash: Optional[str] = None       # SHA-256


def validate_file(
    filename: str,
    content: bytes,
    max_size: int = MAX_FILE_SIZE,
) -> FileValidationResult:
    """完整的文件校验流程.

    1. 扩展名校验
    2. 文件大小校验
    3. 魔数校验（绕过扩展名伪造）
    4. 哈希计算
    """
    file_size = len(content)

    # 1. 扩展名校验
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        return FileValidationResult(
            is_valid=False,
            file_size=file_size,
            error_message="文件缺少扩展名，无法识别文件类型。支持的格式: PDF, DOCX, MD, TXT",
        )

    if ext not in ALLOWED_EXTENSIONS:
        return FileValidationResult(
            is_valid=False,
            file_size=file_size,
            error_message=f"不支持的文件类型 '{ext}'。目前仅支持: PDF, DOCX, MD, TXT",
        )

    # 2. 文件大小校验
    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        return FileValidationResult(
            is_valid=False,
            file_type=ext,
            file_size=file_size,
            error_message=f"文件过大 ({size_mb:.1f}MB)。单个文件上限为 {max_mb:.0f}MB",
        )

    if file_size == 0:
        return FileValidationResult(
            is_valid=False,
            file_type=ext,
            file_size=0,
            error_message="文件为空，无法上传空文件",
        )

    # 3. 魔数校验（对于 PDF 和 DOCX）
    detected_ext = _detect_by_magic(content)
    if detected_ext and detected_ext != ext:
        return FileValidationResult(
            is_valid=False,
            file_size=file_size,
            error_message=f"文件内容与扩展名不匹配。扩展名为 '{ext}'，但文件内容实际为 '{detected_ext}' 格式",
        )

    # 4. SHA-256 哈希
    file_hash = hashlib.sha256(content).hexdigest()

    return FileValidationResult(
        is_valid=True,
        file_type=ext,
        mime_type=MIME_MAP.get(ext),
        file_size=file_size,
        file_hash=file_hash,
    )


def _detect_by_magic(content: bytes) -> Optional[str]:
    """通过文件头魔数检测真实类型."""
    for magic, ext in MAGIC_SIGNATURES.items():
        if content.startswith(magic):
            return ext
    return None


def extract_metadata(filename: str, content: bytes) -> dict:
    """提取文件基础元信息."""
    ext = os.path.splitext(filename)[1].lower()
    meta = {
        "filename": filename,
        "extension": ext,
        "file_size_bytes": len(content),
        "mime_type": MIME_MAP.get(ext, "application/octet-stream"),
        "sha256": hashlib.sha256(content).hexdigest(),
    }

    # PDF: 读取页数（简单实现，精确页数留给解析阶段）
    if ext == ".pdf":
        try:
            meta["page_count"] = _count_pdf_pages(content)
        except Exception:
            meta["page_count"] = None

    return meta


def _count_pdf_pages(content: bytes) -> Optional[int]:
    """快速估算PDF页数（通过统计 /Type /Page 对象）."""
    try:
        text = content.decode("latin-1", errors="ignore")
        import re
        pages = re.findall(r"/Type\s*/Page[^s]", text)
        return len(pages)
    except Exception:
        return None
