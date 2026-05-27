"""Document processing status constants and lifecycle state machine.

Status flow:
    UPLOADED → PARSING → PARSED → CHUNKING → EMBEDDING → INDEXED → READY
    Any stage → FAILED (terminal)
"""

from enum import StrEnum
from typing import Optional


class DocumentStatus(StrEnum):
    """文档处理状态枚举."""

    UPLOADED = "uploaded"       # 已上传，等待处理
    PARSING = "parsing"          # 正在解析文档内容
    PARSED = "parsed"            # 解析完成
    CHUNKING = "chunking"        # 正在分块
    EMBEDDING = "embedding"      # 正在向量化
    INDEXED = "indexed"          # 已写入向量库
    READY = "ready"              # 就绪，可检索
    FAILED = "failed"            # 处理失败（终态）


# 合法的状态流转路径
_TRANSITIONS: dict[DocumentStatus, list[DocumentStatus]] = {
    DocumentStatus.UPLOADED:  [DocumentStatus.PARSING, DocumentStatus.FAILED],
    DocumentStatus.PARSING:   [DocumentStatus.PARSED, DocumentStatus.FAILED],
    DocumentStatus.PARSED:    [DocumentStatus.CHUNKING, DocumentStatus.FAILED],
    DocumentStatus.CHUNKING:  [DocumentStatus.EMBEDDING, DocumentStatus.FAILED],
    DocumentStatus.EMBEDDING: [DocumentStatus.INDEXED, DocumentStatus.FAILED],
    DocumentStatus.INDEXED:   [DocumentStatus.READY, DocumentStatus.FAILED],
    DocumentStatus.READY:     [DocumentStatus.FAILED],
    DocumentStatus.FAILED:    [],  # 终态
}


# 允许重新处理的起始状态
_RETRYABLE_STATUSES = frozenset({DocumentStatus.FAILED, DocumentStatus.PARSED, DocumentStatus.INDEXED, DocumentStatus.READY})


def can_transition(current: str, target: str) -> bool:
    """检查状态是否允许从 current 流转到 target."""
    try:
        cur = DocumentStatus(current)
        tgt = DocumentStatus(target)
    except ValueError:
        return False
    return tgt in _TRANSITIONS.get(cur, [])


def next_status(current: str) -> Optional[DocumentStatus]:
    """返回当前状态的合法下一状态（非 FAILED）."""
    try:
        cur = DocumentStatus(current)
    except ValueError:
        return None
    allowed = _TRANSITIONS.get(cur, [])
    for s in allowed:
        if s != DocumentStatus.FAILED:
            return s
    return None


def is_terminal(status: str) -> bool:
    """终态."""
    return status in (DocumentStatus.READY, DocumentStatus.FAILED)


def is_retryable(status: str) -> bool:
    """是否可以重新处理."""
    return status in _RETRYABLE_STATUSES


def status_display_name(status: str) -> str:
    """返回中文显示名称."""
    mapping = {
        "uploaded": "已上传",
        "parsing": "解析中",
        "parsed": "已解析",
        "chunking": "分块中",
        "embedding": "向量化中",
        "indexed": "已索引",
        "ready": "就绪",
        "failed": "失败",
    }
    return mapping.get(status, status)
