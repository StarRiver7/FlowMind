"""Source Builder — build structured source citations from search results.

Transforms raw Milvus search hits into user-facing source references:
  {
    "document_name": "员工手册.pdf",
    "page": 5,
    "chunk_index": 12,
    "score": 0.91,
    "title_path": "第三章 > 3.2 考勤",
    "excerpt": "员工每日应按时打卡..."
  }
"""

from typing import Optional
from app.core.logger import get_logger

logger = get_logger(__name__)


class SourceBuilder:
    """Build structured source citations from retrieval results."""

    @staticmethod
    def build(chunk: dict, document_name_map: Optional[dict[int, str]] = None) -> dict:
        """Build a single source citation from a search hit.

        Args:
            chunk: Milvus search result dict
            document_name_map: optional {document_id: file_name} mapping

        Returns:
            Structured source citation dict
        """
        doc_id = chunk.get("document_id")
        file_name = "unknown"
        if document_name_map and doc_id in document_name_map:
            file_name = document_name_map[doc_id]

        page = chunk.get("page_number")
        chunk_idx = chunk.get("chunk_index", 0)
        title_path = chunk.get("title_path", "")
        content = chunk.get("content", "")

        # Build display string
        parts = [file_name]
        if page and page > 0:
            parts.append(f"第{page}页")
        parts.append(f"chunk #{chunk_idx}")
        display = " ".join(parts)

        # Excerpt (first 150 chars)
        excerpt = content[:150].replace("\n", " ")
        if len(content) > 150:
            excerpt += "..."

        return {
            "document_id": doc_id,
            "document_name": file_name,
            "page_number": page,
            "chunk_index": chunk_idx,
            "score": round(chunk.get("score", 0), 4),
            "title_path": title_path,
            "display": display,
            "excerpt": excerpt,
            "content": content,
        }

    @staticmethod
    def build_batch(
        chunks: list[dict],
        document_name_map: Optional[dict[int, str]] = None,
    ) -> list[dict]:
        """Build source citations for a batch of search hits."""
        return [SourceBuilder.build(c, document_name_map) for c in chunks]

    @staticmethod
    def deduplicate_sources(sources: list[dict]) -> list[dict]:
        """Remove duplicate sources by document_id + chunk_index."""
        seen = set()
        unique = []
        for s in sources:
            key = (s.get("document_id"), s.get("chunk_index"))
            if key not in seen:
                seen.add(key)
                unique.append(s)
        return unique


source_builder = SourceBuilder()
