"""Chunk Metadata — 每个 Chunk 的完整元数据结构.

每个 Chunk 保存:
  - chunk_id (数据库主键)
  - document_id
  - chunk_index (序号)
  - page_number (源页码)
  - title_path (标题路径)
  - source_text (原始文本引用)
  - token_count (Token 数)
  - char_count (字符数)
  - quality_score (可选质量分)
  - created_time
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ChunkMetadata:
    """Chunk 元数据 — 结构化记录每个分块的全部溯源信息."""

    document_id: int
    chunk_index: int
    content: str
    char_count: int
    token_count: int = 0
    page_number: Optional[int] = None
    title_path: list[str] = field(default_factory=list)
    source_text: str = ""           # 在原文中的起始定位
    quality_score: float = 1.0      # 0-1 质量分
    is_heading_start: bool = False
    overlap_with_prev: bool = False
    created_time: Optional[datetime] = None

    def to_db_dict(self) -> dict:
        """转为 t_document_chunk 写入格式."""
        return {
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "char_count": self.char_count,
            "page_number": self.page_number,
            "milvus_id": None,      # 本阶段不实现
            "is_embedded": 0,        # 本阶段不实现
            "create_time": self.created_time or datetime.now(),
        }

    def to_source_citation(self, file_name: str = "") -> dict:
        """生成 Source 引用数据.

        用于后续 RAG 回答中的 "来源: 员工手册 第5页".
        """
        page_info = f"第{self.page_number}页" if self.page_number else ""
        return {
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "file_name": file_name,
            "page_number": self.page_number,
            "title_path": " > ".join(self.title_path) if self.title_path else "",
            "char_count": self.char_count,
            "token_count": self.token_count,
            "display": f"{file_name} {page_info} (chunk #{self.chunk_index})".strip(),
            "excerpt": self.content[:150] + ("..." if len(self.content) > 150 else ""),
        }


def build_chunk_metadata(
    document_id: int,
    chunk_index: int,
    content: str,
    token_count: int = 0,
    page_number: Optional[int] = None,
    title_path: Optional[list[str]] = None,
    is_heading_start: bool = False,
    overlap_with_prev: bool = False,
) -> ChunkMetadata:
    """工厂方法: 快速构建 ChunkMetadata."""
    return ChunkMetadata(
        document_id=document_id,
        chunk_index=chunk_index,
        content=content,
        char_count=len(content),
        token_count=token_count,
        page_number=page_number,
        title_path=title_path or [],
        source_text=content[:100],
        is_heading_start=is_heading_start,
        overlap_with_prev=overlap_with_prev,
        created_time=datetime.now(),
    )
