"""Tests for Retrieval Engine — Phase 6.4.

Covers:
  1. DenseRetriever (unit)
  2. SparseRetriever / BM25 (unit)
  3. ScoreFusion (unit)
  4. Reranker (unit)
  5. ChunkMerger (unit)
  6. SourceBuilder (extended)
  7. MetadataFilter (extended)
  8. QueryRewrite (unit)
"""

import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ============================================================================
# Test 1: DenseRetriever
# ============================================================================
class TestDenseRetriever:
    """Tests for dense_retriever.py (unit — no Milvus needed)."""

    def test_score_normalization(self):
        from app.rag.retrieval.dense_retriever import DenseRetriever
        results = [
            {"score": 0.9, "content": "A"},
            {"score": 0.5, "content": "B"},
        ]
        normalized = DenseRetriever._normalize_scores(results)
        assert normalized[0]["dense_score"] == 0.9
        assert normalized[1]["dense_score"] == 0.5

    def test_normalize_empty(self):
        from app.rag.retrieval.dense_retriever import DenseRetriever
        assert DenseRetriever._normalize_scores([]) == []

    def test_module_imports(self):
        from app.rag.retrieval.dense_retriever import dense_retriever, DenseRetriever
        assert dense_retriever is not None
        assert isinstance(dense_retriever, DenseRetriever)


# ============================================================================
# Test 2: SparseRetriever / BM25
# ============================================================================
class TestSparseRetriever:
    """Tests for sparse_retriever.py (BM25 keyword search)."""

    def test_tokenize(self):
        from app.rag.retrieval.sparse_retriever import sparse_retriever
        tokens = sparse_retriever.tokenize("员工考勤制度")
        assert len(tokens) >= 1

    def test_build_index(self):
        from app.rag.retrieval.sparse_retriever import sparse_retriever
        candidates = [
            {"content": "员工每日应按时打卡", "title_path": "第三章 考勤"},
            {"content": "年假申请需提前三天", "title_path": "第四章 休假"},
        ]
        tokenized, bm25 = sparse_retriever.build_index(candidates)
        assert bm25 is not None
        assert len(tokenized) == 2

    def test_search_returns_results(self):
        from app.rag.retrieval.sparse_retriever import sparse_retriever
        candidates = [
            {"content": "attendance policy for employees", "title_path": "Chapter 3 Attendance"},
            {"content": "annual leave application process", "title_path": "Chapter 4 Leave"},
            {"content": "attendance exceptions must be reported", "title_path": "Chapter 3 Attendance"},
        ]
        results = sparse_retriever.search("attendance policy", candidates, top_k=3)
        assert len(results) >= 1
        assert all("bm25_score" in r for r in results)

    def test_search_empty_candidates(self):
        from app.rag.retrieval.sparse_retriever import sparse_retriever
        results = sparse_retriever.search("test", [])
        assert results == []

    def test_title_boost(self):
        from app.rag.retrieval.sparse_retriever import sparse_retriever
        candidates = [
            {"content": "paddingtext" * 5, "title_path": "attendance policy"},
            {"content": "attendance policy rules and regulations", "title_path": ""},
        ]
        results = sparse_retriever.search("attendance policy", candidates, top_k=2)
        assert len(results) >= 1


# ============================================================================
# Test 3: ScoreFusion
# ============================================================================
class TestScoreFusion:
    """Tests for score_fusion.py."""

    def test_fuse_weighted_basic(self):
        from app.rag.retrieval.score_fusion import ScoreFusion
        fusion = ScoreFusion(dense_weight=0.7, sparse_weight=0.3)
        dense = [
            {"milvus_pk": 1, "dense_score": 0.9, "content": "A", "score": 0.9},
            {"milvus_pk": 2, "dense_score": 0.5, "content": "B", "score": 0.5},
        ]
        sparse = [
            {"milvus_pk": 1, "sparse_score": 0.8, "content": "A"},
            {"milvus_pk": 2, "sparse_score": 0.2, "content": "B"},
        ]
        fused = fusion.fuse_weighted(dense, sparse)
        assert len(fused) == 2
        assert 0.86 < fused[0]["score"] < 0.88
        assert "dense_score" in fused[0]
        assert "sparse_score" in fused[0]

    def test_fuse_weighted_sparse_only(self):
        from app.rag.retrieval.score_fusion import ScoreFusion
        fusion = ScoreFusion(dense_weight=0.7, sparse_weight=0.3)
        dense = []
        sparse = [
            {"milvus_pk": 1, "sparse_score": 0.9, "content": "A"},
        ]
        fused = fusion.fuse_weighted(dense, sparse)
        assert len(fused) == 1
        assert fused[0]["score"] == pytest.approx(0.27)

    def test_fuse_rrf(self):
        from app.rag.retrieval.score_fusion import ScoreFusion
        fusion = ScoreFusion()
        dense = [
            {"milvus_pk": 1, "content": "A"},
            {"milvus_pk": 2, "content": "B"},
        ]
        sparse = [
            {"milvus_pk": 1, "content": "A"},
        ]
        fused = fusion.fuse_rrf(dense, sparse, k=60)
        assert len(fused) == 2
        assert fused[0]["milvus_pk"] == 1

    def test_deduplicate(self):
        from app.rag.retrieval.score_fusion import ScoreFusion
        fusion = ScoreFusion()
        results = [
            {"content": "same content here", "score": 0.9},
            {"content": "same content here", "score": 0.7},
            {"content": "different one", "score": 0.5},
        ]
        unique = fusion.deduplicate(results)
        assert len(unique) == 2

    def test_fuse_empty(self):
        from app.rag.retrieval.score_fusion import ScoreFusion
        fusion = ScoreFusion()
        assert fusion.fuse_weighted([], []) == []


# ============================================================================
# Test 4: Reranker
# ============================================================================
class TestReranker:
    """Tests for reranker.py."""

    @pytest.mark.asyncio
    async def test_rerank_deduplicates(self):
        from app.rag.retrieval.reranker import reranker
        chunks = [
            {"content": "exact same content here", "score": 0.8},
            {"content": "exact same content here", "score": 0.7},
        ]
        ranked = await reranker.rerank("query", chunks, score_threshold=0.0)
        assert len(ranked) == 1

    @pytest.mark.asyncio
    async def test_rerank_sorts_by_score(self):
        from app.rag.retrieval.reranker import reranker
        chunks = [
            {"content": "low quality text here but enough chars to pass checks", "score": 0.3},
            {"content": "high quality match with lots of content here for testing", "score": 0.95},
            {"content": "medium match text right here for the test suite", "score": 0.6},
        ]
        ranked = await reranker.rerank("test query", chunks, score_threshold=0.0)
        assert ranked[0]["score"] >= ranked[-1]["score"]

    @pytest.mark.asyncio
    async def test_rerank_threshold(self):
        from app.rag.retrieval.reranker import reranker
        chunks = [
            {"content": "x" * 60, "score": 0.2},
            {"content": "This is a high quality match with enough content here to pass checks", "score": 0.9},
        ]
        ranked = await reranker.rerank("query", chunks, score_threshold=0.5)
        assert len(ranked) == 1

    @pytest.mark.asyncio
    async def test_rerank_top_n(self):
        from app.rag.retrieval.reranker import reranker
        chunks = [
            {"content": "chunk content number " + str(i) + " padded with more text to avoid short penalty", "score": 0.9 - i * 0.1}
            for i in range(10)
        ]
        ranked = await reranker.rerank("query", chunks, top_n=3, score_threshold=0.0)
        assert len(ranked) == 3

    @pytest.mark.asyncio
    async def test_rerank_empty(self):
        from app.rag.retrieval.reranker import reranker
        ranked = await reranker.rerank("query", [])
        assert ranked == []

    def test_is_semantic_default(self):
        from app.rag.retrieval.reranker import reranker
        assert reranker.is_semantic is False


# ============================================================================
# Test 5: ChunkMerger
# ============================================================================
class TestChunkMerger:
    """Tests for chunk_merger.py."""

    def test_merge_adjacent(self):
        from app.rag.retrieval.chunk_merger import ChunkMerger
        merger = ChunkMerger()
        chunks = [
            {"document_id": 1, "chunk_index": 0, "content": "Paragraph one.", "score": 0.8, "page_number": 1},
            {"document_id": 1, "chunk_index": 1, "content": "Paragraph two.", "score": 0.7, "page_number": 1},
            {"document_id": 1, "chunk_index": 2, "content": "Paragraph three.", "score": 0.9, "page_number": 2},
        ]
        merged = merger.merge(chunks)
        assert len(merged) == 1
        assert merged[0]["merge_count"] == 3
        assert "Paragraph one." in merged[0]["content"]
        assert "Paragraph three." in merged[0]["content"]
        assert merged[0]["score"] == 0.9

    def test_merge_different_docs_stay_separate(self):
        from app.rag.retrieval.chunk_merger import ChunkMerger
        merger = ChunkMerger()
        chunks = [
            {"document_id": 1, "chunk_index": 0, "content": "Doc1 A.", "score": 0.8},
            {"document_id": 2, "chunk_index": 0, "content": "Doc2 A.", "score": 0.7},
            {"document_id": 1, "chunk_index": 1, "content": "Doc1 B.", "score": 0.6},
        ]
        merged = merger.merge(chunks)
        # Doc1 with chunks 0,1 merged (one block); Doc2 separate (another block)
        assert len(merged) == 2

    def test_merge_non_adjacent_stay_separate(self):
        from app.rag.retrieval.chunk_merger import ChunkMerger
        merger = ChunkMerger()
        chunks = [
            {"document_id": 1, "chunk_index": 0, "content": "A.", "score": 0.8},
            {"document_id": 1, "chunk_index": 5, "content": "B.", "score": 0.7},
        ]
        merged = merger.merge(chunks)
        assert len(merged) == 2

    def test_merge_score_keeps_best(self):
        from app.rag.retrieval.chunk_merger import ChunkMerger
        merger = ChunkMerger()
        chunks = [
            {"document_id": 1, "chunk_index": 0, "content": "A.", "score": 0.3},
            {"document_id": 1, "chunk_index": 1, "content": "B.", "score": 0.95},
        ]
        merged = merger.merge(chunks)
        assert merged[0]["score"] == 0.95

    def test_merge_empty(self):
        from app.rag.retrieval.chunk_merger import ChunkMerger
        merger = ChunkMerger()
        assert merger.merge([]) == []
        single_result = merger.merge([{"content": "only one", "document_id": 1, "chunk_index": 0, "score": 0.5}])
        assert len(single_result) == 1
        assert single_result[0]["merge_count"] == 1
        assert single_result[0]["content"] == "only one"

    def test_merge_page_range(self):
        from app.rag.retrieval.chunk_merger import ChunkMerger
        merger = ChunkMerger()
        chunks = [
            {"document_id": 1, "chunk_index": 0, "content": "Page 1.", "score": 0.8, "page_number": 1},
            {"document_id": 1, "chunk_index": 1, "content": "Page 2.", "score": 0.7, "page_number": 2},
        ]
        merged = merger.merge(chunks)
        assert merged[0]["page_range"] == [1, 2]

    def test_merge_with_window(self):
        from app.rag.retrieval.chunk_merger import ChunkMerger
        merger = ChunkMerger()
        chunks = [
            {"document_id": 1, "chunk_index": 0, "content": "A.", "score": 0.9},
            {"document_id": 1, "chunk_index": 2, "content": "B.", "score": 0.8},
        ]
        merged_default = merger.merge(chunks)
        assert len(merged_default) == 2
        merged_window = merger.merge_with_window(chunks, window_size=3)
        assert len(merged_window) == 1


# ============================================================================
# Test 6: SourceBuilder (extended)
# ============================================================================
class TestSourceBuilderExtended:
    """Extended tests for upgraded source_builder.py."""

    def test_build_with_kb_name(self):
        from app.rag.retrieval.source_builder import SourceBuilder
        chunk = {
            "document_id": 1, "page_number": 5,
            "chunk_index": 3, "score": 0.85,
            "content": "Employee must clock in before 9am.",
            "title_path": "Chapter 3",
            "space_id": 1,
        }
        kb_map = {1: "HR知识库"}
        src = SourceBuilder.build(chunk, kb_name_map=kb_map)
        assert src["knowledge_base"] == "HR知识库"
        assert src["knowledge_base_id"] == 1

    def test_build_with_page_range(self):
        from app.rag.retrieval.source_builder import SourceBuilder
        chunk = {
            "document_id": 1, "page_number": 3,
            "chunk_index": 0, "score": 0.9,
            "content": "Merged content.",
            "page_range": [3, 4, 5],
            "merge_count": 3,
        }
        src = SourceBuilder.build(chunk)
        assert src["page_range"] == [3, 4, 5]
        assert src["merge_count"] == 3
        assert "第3-5页" in src["display"]

    def test_format_for_display(self):
        from app.rag.retrieval.source_builder import SourceBuilder
        sources = [
            {"document_id": 1, "document_name": "员工手册.pdf", "page_number": 5,
             "knowledge_base": "HR知识库", "score": 0.92, "chunk_index": 0, "content": "..."},
        ]
        formatted = SourceBuilder.format_for_display(sources)
        assert len(formatted) == 1
        assert "员工手册.pdf" in formatted[0]
        assert "第5页" in formatted[0]

    def test_kb_name_cache(self):
        from app.rag.retrieval.source_builder import SourceBuilder
        SourceBuilder.set_kb_name_cache({1: "HR知识库", 2: "技术文档"})
        assert SourceBuilder.get_kb_name(1) == "HR知识库"
        assert SourceBuilder.get_kb_name(2) == "技术文档"
        assert SourceBuilder.get_kb_name(99) == "知识库#99"


# ============================================================================
# Test 7: MetadataFilter (extended)
# ============================================================================
class TestMetadataFilterExtended:
    """Additional metadata filter tests."""

    def test_filter_respects_visibility_private(self):
        from app.rag.vector_store.metadata_filter import MetadataFilter
        expr = MetadataFilter.build_access_filter(user_id=5, department_id=None)
        assert "public" in expr
        assert "creator_id == 5" in expr

    def test_filter_with_multiple_spaces(self):
        from app.rag.vector_store.metadata_filter import MetadataFilter
        expr = MetadataFilter.build_space_filter([1, 2, 3, 4, 5])
        assert "space_id in [1, 2, 3, 4, 5]" in expr

    def test_combined_filter_comprehensive(self):
        from app.rag.vector_store.metadata_filter import MetadataFilter
        expr = MetadataFilter.build_combined_filter(
            user_id=10,
            department_id=20,
            space_ids=[1, 2],
            document_ids=[100, 200],
        )
        assert expr is not None
        assert "space_id" in expr
        assert "document_id" in expr
        assert "department_id == 20" in expr


# ============================================================================
# Test 8: QueryRewrite (unit)
# ============================================================================
class TestQueryRewrite:
    """Tests for query_rewrite.py (LLM calls skipped in unit tests)."""

    @pytest.mark.asyncio
    async def test_skip_short_query(self):
        from app.rag.retrieval.query_rewrite import QueryRewriter
        rewriter = QueryRewriter()
        result = await rewriter.rewrite("ab")
        assert result == "ab"

    @pytest.mark.asyncio
    async def test_skip_long_query(self):
        from app.rag.retrieval.query_rewrite import QueryRewriter
        rewriter = QueryRewriter()
        long_query = "x" * 60
        result = await rewriter.rewrite(long_query)
        assert result == long_query

    @pytest.mark.asyncio
    async def test_rewrite_module_imports(self):
        from app.rag.retrieval.query_rewrite import query_rewriter, QueryRewriter
        assert query_rewriter is not None
        assert isinstance(query_rewriter, QueryRewriter)
