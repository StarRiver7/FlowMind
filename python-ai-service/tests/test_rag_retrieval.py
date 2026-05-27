import sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

class TestEmbeddingCache:
    def test_cache_put_get(self):
        from app.rag.embedding.embedding_cache import EmbeddingCache
        cache = EmbeddingCache(max_size=100)
        cache.put("hello", [0.1, 0.2, 0.3])
        result = cache.get("hello")
        assert result == [0.1, 0.2, 0.3]
        assert cache.get("nonexistent") is None

    def test_cache_stats(self):
        from app.rag.embedding.embedding_cache import EmbeddingCache
        cache = EmbeddingCache(max_size=100)
        cache.put("a", [1.0])
        cache.get("a")
        cache.get("b")
        assert cache.stats["hits"] == 1
        assert cache.stats["misses"] == 1

    def test_cache_batch(self):
        from app.rag.embedding.embedding_cache import EmbeddingCache
        cache = EmbeddingCache(max_size=100)
        cache.put("a", [1.0])
        cache.put("c", [3.0])
        cached, missing = cache.get_batch(["a", "b", "c"])
        assert cached[0] == [1.0]
        assert cached[1] is None
        assert cached[2] == [3.0]
        assert missing == [1]

    def test_cache_eviction(self):
        from app.rag.embedding.embedding_cache import EmbeddingCache
        cache = EmbeddingCache(max_size=3)
        for i in range(5):
            cache.put(f"key{i}", [float(i)])
        assert cache.size == 3

    def test_cache_clear(self):
        from app.rag.embedding.embedding_cache import EmbeddingCache
        cache = EmbeddingCache(max_size=100)
        cache.put("x", [0.0])
        cache.clear()
        assert cache.size == 0

class TestMetadataFilter:
    def test_build_access_filter_public(self):
        from app.rag.vector_store.metadata_filter import MetadataFilter
        expr = MetadataFilter.build_access_filter(user_id=1, department_id=None)
        assert "public" in expr
        assert "creator_id == 1" in expr

    def test_build_access_filter_department(self):
        from app.rag.vector_store.metadata_filter import MetadataFilter
        expr = MetadataFilter.build_access_filter(user_id=1, department_id=10)
        assert "department_id == 10" in expr

    def test_build_space_filter(self):
        from app.rag.vector_store.metadata_filter import MetadataFilter
        expr = MetadataFilter.build_space_filter([1, 2, 3])
        assert "space_id in [1, 2, 3]" in expr

    def test_build_document_filter(self):
        from app.rag.vector_store.metadata_filter import MetadataFilter
        expr = MetadataFilter.build_document_filter([42, 43])
        assert "document_id in [42, 43]" in expr

    def test_build_combined_filter(self):
        from app.rag.vector_store.metadata_filter import MetadataFilter
        expr = MetadataFilter.build_combined_filter(
            user_id=1, department_id=10, space_ids=[1, 2],
        )
        assert expr is not None
        assert "space_id" in expr
        assert "public" in expr

class TestSourceBuilder:
    def test_build_source(self):
        from app.rag.retrieval.source_builder import SourceBuilder
        chunk = {
            "document_id": 1, "page_number": 5,
            "chunk_index": 3, "score": 0.85,
            "content": "Employee must clock in before 9am.",
            "title_path": "Chapter 3",
        }
        src = SourceBuilder.build(chunk)
        assert src["document_id"] == 1
        assert src["page_number"] == 5
        assert src["chunk_index"] == 3
        assert src["score"] == 0.85
        assert "chunk #3" in src["display"]

    def test_deduplicate_sources(self):
        from app.rag.retrieval.source_builder import SourceBuilder
        sources = [
            {"document_id": 1, "chunk_index": 0, "content": "A"},
            {"document_id": 1, "chunk_index": 0, "content": "A"},
            {"document_id": 1, "chunk_index": 1, "content": "B"},
        ]
        unique = SourceBuilder.deduplicate_sources(sources)
        assert len(unique) == 2

    def test_build_batch(self):
        from app.rag.retrieval.source_builder import SourceBuilder
        chunks = [
            {"document_id": 1, "page_number": 1, "chunk_index": 0, "score": 0.9, "content": "X", "title_path": ""},
            {"document_id": 1, "page_number": 2, "chunk_index": 1, "score": 0.8, "content": "Y", "title_path": ""},
        ]
        sources = SourceBuilder.build_batch(chunks)
        assert len(sources) == 2

class TestRetrievalContext:
    def test_build_context(self):
        from app.rag.retrieval.retrieval_context import RetrievalContext
        ctx = RetrievalContext(max_tokens=500)
        chunks = [
            {"document_id": 1, "page_number": 1, "chunk_index": 0, "score": 0.9,
             "content": "This is a test chunk content for retrieval.", "title_path": ""},
        ]
        result = ctx.build(chunks)
        assert "Source 1" in result["context_text"]
        assert result["total_chunks"] == 1
        assert len(result["sources"]) == 1

    def test_context_truncation(self):
        from app.rag.retrieval.retrieval_context import RetrievalContext
        ctx = RetrievalContext(max_tokens=10)  # Very small budget
        chunks = [
            {"document_id": 1, "page_number": 1, "chunk_index": 0, "score": 0.9,
             "content": "X" * 500, "title_path": ""},
        ] * 10
        result = ctx.build(chunks)
        assert result["truncated"] or result["included_chunks"] < 10

    def test_compact(self):
        from app.rag.retrieval.retrieval_context import RetrievalContext
        ctx = RetrievalContext()
        chunks = [
            {"document_id": 1, "page_number": 1, "chunk_index": 0, "score": 0.9,
             "content": "Content A", "title_path": ""},
        ]
        compact = ctx.build_compact(chunks)
        assert "Content A" in compact

class TestRetrievalRanker:
    @pytest.mark.asyncio
    async def test_rank_sorts_by_score(self):
        from app.rag.retrieval.retrieval_ranker import retrieval_ranker
        chunks = [
            {"content": "low", "score": 0.3},
            {"content": "high", "score": 0.9},
            {"content": "mid", "score": 0.6},
        ]
        ranked = await retrieval_ranker.rank("query", chunks, score_threshold=0.0)
        assert ranked[0]["score"] == 0.9
        assert ranked[-1]["score"] == 0.3

    @pytest.mark.asyncio
    async def test_rank_deduplicates(self):
        from app.rag.retrieval.retrieval_ranker import retrieval_ranker
        chunks = [
            {"content": "same text here", "score": 0.8},
            {"content": "same text here", "score": 0.7},
        ]
        ranked = await retrieval_ranker.rank("query", chunks, score_threshold=0.0)
        assert len(ranked) == 1

    @pytest.mark.asyncio
    async def test_rank_threshold(self):
        from app.rag.retrieval.retrieval_ranker import retrieval_ranker
        chunks = [
            {"content": "low", "score": 0.2},
            {"content": "high", "score": 0.8},
        ]
        ranked = await retrieval_ranker.rank("query", chunks, score_threshold=0.5)
        assert len(ranked) == 1
        assert ranked[0]["score"] == 0.8
