"""Citation module — traceable source citations for enterprise RAG.

Every AI answer that references knowledge base content must include
citations that can be traced back to specific documents, pages, and chunks.

Key components:
  - CitationBuilder: constructs Citation objects from retrieval results
  - SourceManager: aggregates, deduplicates, and fuses sources
  - SourceFormatter: formats citations for display (inline, list, markdown)
  - SourceHighlighter: maps citations to text spans for frontend highlighting
  - Citation / CitationSet: canonical data models
"""

from app.rag.citation.citation_models import (
    Citation, CitationSet, SourceTrust, SOURCE_TRUST_MAP,
)
from app.rag.citation.citation_builder import citation_builder, CitationBuilder
from app.rag.citation.source_manager import source_manager, SourceManager
from app.rag.citation.source_formatter import source_formatter, SourceFormatter
from app.rag.citation.source_highlighter import source_highlighter, SourceHighlighter
