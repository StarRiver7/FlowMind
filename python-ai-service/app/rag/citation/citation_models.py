"""Citation Models — data structures for source citations.

Defines the canonical citation format used throughout the system.
Every AI answer that references knowledge base content must include
citations conforming to this schema.

Key principle: traceability.
  - Every claim can be traced back to a specific document, page, and chunk
  - Citations carry trust metadata (score, document type, recency)
  - Multiple citations per answer are ordered by relevance
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Citation:
    """A single source citation with full traceability metadata.

    Example:
        Citation(
            citation_id=1,
            document_id=42,
            document_name="员工手册.pdf",
            knowledge_base="HR知识库",
            knowledge_base_id=1,
            page_number=5,
            chunk_index=12,
            chunk_id="doc_42_chunk_12",
            relevance_score=0.94,
            quote_text="年假需提前3天向直属领导申请",
            title_path="第四章 休假制度 > 4.1 年假申请",
            source_type="official",
        )
    """

    citation_id: int
    document_id: int
    document_name: str
    knowledge_base: str = ""
    knowledge_base_id: int = 0
    page_number: int = 0
    page_number_end: Optional[int] = None
    chunk_index: int = 0
    chunk_id: str = ""
    relevance_score: float = 0.0
    quote_text: str = ""
    full_content: str = ""
    title_path: str = ""
    source_type: str = "document"  # official | department | user_upload
    retrieval_score: float = 0.0
    rerank_score: float = 0.0
    composite_score: float = 0.0
    merge_count: int = 1
    created_time: Optional[datetime] = None

    def display_ref(self) -> str:
        """Human-readable citation reference marker."""
        if self.page_number > 0:
            return f"《{self.document_name}》第{self.page_number}页"
        return f"《{self.document_name}》"

    def inline_marker(self) -> str:
        """Inline citation marker like [1]"""
        return f"[{self.citation_id}]"

    def to_dict(self) -> dict:
        """Serialize to dict for API responses."""
        return {
            "citation_id": self.citation_id,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "knowledge_base": self.knowledge_base,
            "knowledge_base_id": self.knowledge_base_id,
            "page_number": self.page_number,
            "page_number_end": self.page_number_end,
            "chunk_index": self.chunk_index,
            "chunk_id": self.chunk_id,
            "relevance_score": round(self.relevance_score, 4),
            "quote_text": self.quote_text,
            "title_path": self.title_path,
            "source_type": self.source_type,
            "retrieval_score": round(self.retrieval_score, 4),
            "rerank_score": round(self.rerank_score, 4),
            "composite_score": round(self.composite_score, 4),
            "merge_count": self.merge_count,
            "display_ref": self.display_ref(),
            "inline_marker": self.inline_marker(),
        }


@dataclass
class CitationSet:
    """A collection of citations for one AI answer.

    Ordered by relevance. Supports deduplication and trust scoring.
    """

    citations: list[Citation] = field(default_factory=list)
    answer_query: str = ""
    total_retrieved: int = 0
    trust_level: str = "medium"  # high | medium | low | unreliable

    @property
    def count(self) -> int:
        return len(self.citations)

    @property
    def primary_source(self) -> Optional[Citation]:
        """The most relevant citation."""
        return self.citations[0] if self.citations else None

    @property
    def has_high_trust(self) -> bool:
        """Whether any citation has high relevance."""
        return any(c.relevance_score >= 0.7 for c in self.citations)

    def to_dict(self) -> dict:
        return {
            "citations": [c.to_dict() for c in self.citations],
            "count": self.count,
            "trust_level": self.trust_level,
            "primary_source": self.primary_source.to_dict() if self.primary_source else None,
        }


@dataclass
class SourceTrust:
    """Trust classification for document sources."""

    source_type: str  # official | department | user_upload
    trust_multiplier: float = 1.0
    label: str = ""

    def __post_init__(self):
        if self.source_type == "official":
            self.trust_multiplier = 1.0
            self.label = "公司官方制度"
        elif self.source_type == "department":
            self.trust_multiplier = 0.9
            self.label = "部门文档"
        elif self.source_type == "user_upload":
            self.trust_multiplier = 0.75
            self.label = "用户上传文档"
        else:
            self.trust_multiplier = 0.7
            self.label = "其他来源"


# Trust classification lookup
SOURCE_TRUST_MAP = {
    "official": SourceTrust("official"),
    "department": SourceTrust("department"),
    "user_upload": SourceTrust("user_upload"),
}
