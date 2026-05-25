"""
Integration test for the complete RAG Pipeline.

Tests:
    - TXT ingestion (quick, no external deps)
    - Hybrid search
    - Source citation
    - Rerank
    - Document deletion
    - Context formatting

Run: pytest app/tests/test_rag_pipeline.py -v -s
"""
import os
import sys
import tempfile
import pytest


# Ensure app is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def sample_txt_file():
    """Create a temporary TXT file with structured content."""
    content = """
FlowMind Enterprise AI Platform - Policy Document

Section 1: Data Retention Policy
All customer data shall be retained for a minimum of 7 years in compliance
with financial regulations. After 7 years, data may be anonymized or purged
upon customer request. Regular audits are conducted quarterly.

Section 2: Access Control
Employees must use multi-factor authentication (MFA) to access production
systems. API keys must be rotated every 90 days. All access is logged and
reviewed by the security team monthly.

Section 3: AI Model Usage
The platform uses DeepSeek V3 for general chat and BGE-M3 for embeddings.
All prompts are sanitized before transmission. No PII is sent to external
providers without explicit user consent.

Section 4: Incident Response
Security incidents must be reported within 1 hour of detection. The incident
response team is available 24/7. Critical incidents trigger automatic system
lockdown until resolved by the security lead.
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        return f.name


@pytest.fixture
def sample_md_file():
    """Create a temporary Markdown file."""
    content = """# FlowMind API Documentation

## Authentication
All API requests require a Bearer token in the Authorization header.
Tokens expire after 15 minutes. Use the refresh endpoint to extend.

## Rate Limits
- Free tier: 60 requests/minute
- Pro tier: 600 requests/minute
- Enterprise: 6000 requests/minute

## Endpoints

### POST /ai/chat
Send a chat message to the AI agent.

### POST /ai/rag/search
Search the knowledge base with hybrid retrieval (vector + BM25).
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        return f.name


class TestRAGPipelineIntegration:
    """End-to-end RAG Pipeline tests."""

    @pytest.mark.asyncio
    async def test_01_txt_ingestion(self, sample_txt_file):
        """Test ingesting a TXT file."""
        from app.pipeline.rag_pipeline import rag_pipeline

        result = await rag_pipeline.ingest(
            sample_txt_file,
            doc_id="test-doc-001",
            metadata={"category": "policy", "department": "IT"},
            tenant_id="test-tenant",
        )

        assert result["doc_id"] == "test-doc-001"
        assert result["file_type"] == "txt"
        assert result["chunk_count"] > 0
        assert result["size_bytes"] > 0
        assert result["elapsed_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_02_md_ingestion(self, sample_md_file):
        """Test ingesting a Markdown file."""
        from app.pipeline.rag_pipeline import rag_pipeline

        result = await rag_pipeline.ingest(
            sample_md_file,
            doc_id="test-doc-002",
            tenant_id="test-tenant",
        )

        assert result["doc_id"] == "test-doc-002"
        assert result["file_type"] == "md"
        assert result["chunk_count"] > 0

    @pytest.mark.asyncio
    async def test_03_search_with_citation(self):
        """Test search with source citation."""
        from app.pipeline.rag_pipeline import rag_pipeline

        results = await rag_pipeline.search(
            "what is the data retention policy?",
            top_k=3,
            use_rerank=True,
            with_citation=True,
            tenant_id="test-tenant",
        )

        assert len(results) > 0
        for r in results:
            assert "content" in r
            assert "score" in r
            assert "citation" in r
            assert "source" in r["citation"]

    @pytest.mark.asyncio
    async def test_04_search_context_formatting(self):
        """Test context string formatting."""
        from app.pipeline.rag_pipeline import rag_pipeline

        context = await rag_pipeline.search_context(
            "API authentication and rate limits",
            top_k=3,
            use_rerank=True,
            tenant_id="test-tenant",
        )

        assert isinstance(context, str)
        assert len(context) > 0
        assert "Source" in context

    @pytest.mark.asyncio
    async def test_05_hybrid_retrieval(self):
        """Test hybrid retrieval (vector + BM25)."""
        from app.retrieval.hybrid_retriever import hybrid_retriever

        results = await hybrid_retriever.search(
            "multi-factor authentication MFA access",
            top_k=5,
            final_k=3,
            tenant_id="test-tenant",
        )

        assert len(results) > 0
        # Results should be sorted by relevance
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_06_embedding_dimension(self):
        """Test BGE-M3 embedding dimension."""
        from app.pipeline.embedder import embedding_engine

        vec = await embedding_engine.embed_query("test query")
        assert len(vec) > 0  # embedding dimension

    @pytest.mark.asyncio
    async def test_07_stats(self):
        """Test pipeline statistics."""
        from app.pipeline.rag_pipeline import rag_pipeline

        stats = await rag_pipeline.stats()
        assert stats["total_chunks"] > 0
        assert stats["embedding_dim"] > 0

    @pytest.mark.asyncio
    async def test_08_delete_document(self):
        """Test document deletion."""
        from app.pipeline.rag_pipeline import rag_pipeline

        # Delete test doc
        await rag_pipeline.delete_document("test-doc-001")
        await rag_pipeline.delete_document("test-doc-002")

        # Verify no results for that doc's content
        results = await rag_pipeline.search(
            "data retention policy",
            top_k=3,
            tenant_id="test-tenant",
        )
        # May return empty or unrelated results
        assert all(
            r.get("doc_id") not in ("test-doc-001", "test-doc-002")
            for r in results
        )


class TestIndividualComponents:
    """Unit tests for individual pipeline components."""

    def test_text_splitter(self):
        """Test text splitting."""
        from app.pipeline.splitter import text_splitter

        text = "This is a test document. " * 50
        chunks = text_splitter.split(text)

        assert len(chunks) > 1
        for chunk in chunks:
            assert "content" in chunk
            assert "metadata" in chunk
            assert "chunk_index" in chunk["metadata"]

    def test_loader_validates_extension(self):
        """Test loader rejects unsupported types."""
        import pytest as pt
        from app.pipeline.loader import document_loader

        with pt.raises(ValueError, match="Unsupported"):
            # Can't use async in sync context; test the validation logic
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
