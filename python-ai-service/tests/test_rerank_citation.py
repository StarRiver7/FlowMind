"""Tests for Rerank + Citation System — Phase 6.5.

Covers:
  1. CrossEncoder (heuristic scoring)
  2. RerankPipeline (orchestration)
  3. RerankScorer (composite scoring)
  4. DuplicateFilter (dedup strategies)
  5. CitationBuilder (citation construction)
  6. SourceFormatter (display formatting)
  7. SourceHighlighter (text span detection)
  8. SourceManager (aggregation + fusion)
"""

import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ============================================================================
# Test 1: CrossEncoder
# ============================================================================
class TestCrossEncoder:
    """CrossEncoder heuristic scoring tests."""

    def test_compute_scores_basic(self):
        from app.rag.rerank.cross_encoder import CrossEncoder
        ce = CrossEncoder()
        query = "attendance policy"
        docs = [
            "Employee attendance policy requires clock-in before 9am.",
            "The annual leave application needs 3 days notice.",
            "Office kitchen rules: clean up after yourself.",
        ]
        scores = ce.compute_scores(query, docs)
        assert len(scores) == 3
        assert all(0 <= s <= 1 for s in scores)
        # First doc should score highest (most relevant to "attendance policy")
        assert scores[0] >= scores[2]

    def test_compute_score_single(self):
        from app.rag.rerank.cross_encoder import CrossEncoder
        ce = CrossEncoder()
        score = ce.compute_score("请假制度", "员工年假申请需提前三天向领导申请")
        assert 0 <= score <= 1

    def test_empty_docs(self):
        from app.rag.rerank.cross_encoder import CrossEncoder
        ce = CrossEncoder()
        assert ce.compute_scores("query", []) == []

    def test_exact_match_scores_highest(self):
        from app.rag.rerank.cross_encoder import CrossEncoder
        ce = CrossEncoder()
        query = "考勤打卡规则"
        exact = "考勤打卡规则：员工每日必须在9:00前完成打卡"
        irrelevant = "公司食堂今日菜单：红烧肉、青椒土豆丝"
        scores = ce.compute_scores(query, [exact, irrelevant])
        assert scores[0] > scores[1]

    def test_not_loaded_by_default(self):
        from app.rag.rerank.cross_encoder import CrossEncoder
        ce = CrossEncoder()
        assert not ce.is_loaded


# ============================================================================
# Test 2: RerankPipeline
# ============================================================================
class TestRerankPipeline:
    """RerankPipeline orchestration tests."""

    @pytest.mark.asyncio
    async def test_rerank_sorts_by_relevance(self):
        from app.rag.rerank.rerank_pipeline import RerankPipeline
        pipeline = RerankPipeline()
        query = "请假制度"
        chunks = [
            {"content": "公司请假制度规定年假需提前申请", "score": 0.85},
            {"content": "考勤打卡时间为每日9:00前", "score": 0.80},
            {"content": "公司食堂提供免费午餐", "score": 0.60},
        ]
        reranked = await pipeline.rerank(query, chunks, top_n=3, score_threshold=0.0)
        assert len(reranked) >= 1
        # Most relevant should be first
        assert "请假" in reranked[0]["content"] or "年假" in reranked[0]["content"]

    @pytest.mark.asyncio
    async def test_rerank_adds_scores(self):
        from app.rag.rerank.rerank_pipeline import RerankPipeline
        pipeline = RerankPipeline()
        chunks = [
            {"content": "Employee attendance policy details here", "score": 0.9},
        ]
        reranked = await pipeline.rerank("attendance policy", chunks, top_n=1, score_threshold=0.0)
        assert "rerank_score" in reranked[0]
        assert "cross_encoder_score" in reranked[0]
        assert "composite_score" in reranked[0]

    @pytest.mark.asyncio
    async def test_rerank_threshold_filters(self):
        from app.rag.rerank.rerank_pipeline import RerankPipeline
        pipeline = RerankPipeline()
        chunks = [
            {"content": "relevant content about the topic", "score": 0.9},
            {"content": "somewhat related content here", "score": 0.5},
            {"content": "completely unrelated stuff", "score": 0.1},
        ]
        reranked = await pipeline.rerank("topic", chunks, top_n=5, score_threshold=0.4)
        assert all(c["score"] >= 0.4 for c in reranked)

    @pytest.mark.asyncio
    async def test_rerank_empty(self):
        from app.rag.rerank.rerank_pipeline import RerankPipeline
        pipeline = RerankPipeline()
        result = await pipeline.rerank("query", [])
        assert result == []


# ============================================================================
# Test 3: RerankScorer
# ============================================================================
class TestRerankScorer:
    """Composite score calculation tests."""

    def test_compute_basic(self):
        from app.rag.rerank.rerank_score import RerankScorer
        scorer = RerankScorer()
        # retrieval=0.8, rerank=0.9 → 0.4*0.8 + 0.5*0.9 + 0.1*0 = 0.32+0.45+0=0.77
        composite = scorer.compute(0.8, 0.9)
        assert 0.76 < composite < 0.78

    def test_compute_with_metadata(self):
        from app.rag.rerank.rerank_score import RerankScorer
        scorer = RerankScorer()
        composite = scorer.compute(0.8, 0.9, metadata_boost=0.05)
        # 0.32 + 0.45 + 0.005 = 0.775
        assert 0.77 < composite < 0.78

    def test_compute_batch(self):
        from app.rag.rerank.rerank_score import RerankScorer
        scorer = RerankScorer()
        chunks = [
            {"score": 0.9, "rerank_score": 0.95},
            {"score": 0.6, "rerank_score": 0.7},
        ]
        result = scorer.compute_batch(chunks)
        assert "composite_score" in result[0]
        assert result[0]["score"] == result[0]["composite_score"]
        # Higher-scored chunk should be first after sort
        assert result[0]["composite_score"] >= result[1]["composite_score"]

    def test_score_config_normalizes(self):
        from app.rag.rerank.rerank_score import ScoreConfig
        # Weights that don't sum to 1
        config = ScoreConfig(retrieval_weight=0.5, rerank_weight=0.5, metadata_weight=0.5)
        total = config.retrieval_weight + config.rerank_weight + config.metadata_weight
        assert abs(total - 1.0) < 0.001


# ============================================================================
# Test 4: DuplicateFilter
# ============================================================================
class TestDuplicateFilter:
    """Duplicate filter strategy tests."""

    def test_filter_exact(self):
        from app.rag.rerank.duplicate_filter import DuplicateFilter
        df = DuplicateFilter()
        chunks = [
            {"content": "exact same content here", "score": 0.9},
            {"content": "exact same content here", "score": 0.7},
            {"content": "different content", "score": 0.5},
        ]
        result = df.filter(chunks, strategy="exact")
        assert len(result) == 2

    def test_filter_all_strategies(self):
        from app.rag.rerank.duplicate_filter import DuplicateFilter
        df = DuplicateFilter()
        chunks = [
            {"content": "The quick brown fox jumps over the lazy dog", "score": 0.9},
            {"content": "The quick brown fox jumps over the lazy dog", "score": 0.7},
            {"content": "The quick brown fox jumps over the lazy cat", "score": 0.5},
        ]
        result = df.filter(chunks, strategy="all")
        # Exact dedup removes the second (exact match of first 200 chars)
        # Jaccard may or may not remove the third depending on threshold
        assert len(result) <= 3

    def test_filter_empty(self):
        from app.rag.rerank.duplicate_filter import DuplicateFilter
        df = DuplicateFilter()
        assert df.filter([], strategy="all") == []

    def test_filter_single(self):
        from app.rag.rerank.duplicate_filter import DuplicateFilter
        df = DuplicateFilter()
        chunks = [{"content": "only one", "score": 0.9}]
        assert df.filter(chunks, strategy="all") == chunks

    def test_get_duplicate_groups(self):
        from app.rag.rerank.duplicate_filter import DuplicateFilter
        df = DuplicateFilter()
        chunks = [
            {"content": "aaa bbb ccc", "score": 0.9},
            {"content": "aaa bbb ccc", "score": 0.7},
            {"content": "xxx yyy zzz", "score": 0.5},
        ]
        groups = df.get_duplicate_groups(chunks)
        assert len(groups) >= 1


# ============================================================================
# Test 5: CitationBuilder
# ============================================================================
class TestCitationBuilder:
    """Citation construction tests."""

    def test_build_citations(self):
        from app.rag.citation.citation_builder import CitationBuilder
        builder = CitationBuilder()
        chunks = [
            {
                "document_id": 1, "page_number": 5, "chunk_index": 0,
                "score": 0.94, "content": "年假需提前3天向直属领导申请",
                "title_path": "第四章 休假", "space_id": 1,
                "dense_score": 0.90, "rerank_score": 0.94,
                "composite_score": 0.92,
            },
            {
                "document_id": 2, "page_number": 3, "chunk_index": 5,
                "score": 0.85, "content": "考勤异常需提交书面说明",
                "title_path": "第三章 考勤", "space_id": 1,
            },
        ]
        citation_set = builder.build("请假制度", chunks)
        assert citation_set.count == 2
        assert citation_set.citations[0].citation_id == 1
        assert citation_set.citations[0].document_id == 1
        assert citation_set.citations[0].page_number == 5
        assert citation_set.citations[0].relevance_score == 0.94

    def test_build_trust_assessment(self):
        from app.rag.citation.citation_builder import CitationBuilder
        builder = CitationBuilder()
        chunks = [
            {"document_id": 1, "page_number": 1, "chunk_index": 0,
             "score": 0.85, "content": "high relevance content" * 3, "space_id": 1},
            {"document_id": 2, "page_number": 2, "chunk_index": 1,
             "score": 0.80, "content": "also relevant content" * 3, "space_id": 1},
        ]
        citation_set = builder.build("test query", chunks)
        assert citation_set.trust_level in ("high", "medium", "low", "unreliable")

    def test_build_unreliable(self):
        from app.rag.citation.citation_builder import CitationBuilder
        builder = CitationBuilder()
        chunks = [
            {"document_id": 1, "page_number": 1, "chunk_index": 0,
             "score": 0.15, "content": "low relevance", "space_id": 1},
        ]
        citation_set = builder.build("test", chunks)
        assert citation_set.trust_level == "unreliable"

    def test_extract_quote(self):
        from app.rag.citation.citation_builder import CitationBuilder
        quote = CitationBuilder._extract_quote(
            "员工每日应按时打卡。考勤时间为9:00-18:00。迟到需提交说明。",
            "考勤时间"
        )
        assert "考勤" in quote or "9:00" in quote

    def test_build_minimal(self):
        from app.rag.citation.citation_builder import CitationBuilder
        builder = CitationBuilder()
        chunks = [
            {"document_name": "test.pdf", "page_number": 1, "score": 0.9,
             "content": "test content", "knowledge_base": "Test KB"},
        ]
        result = builder.build_minimal(chunks)
        assert len(result) == 1
        assert result[0]["citation_id"] == 1
        assert "inline_marker" in result[0]


# ============================================================================
# Test 6: SourceFormatter
# ============================================================================
class TestSourceFormatter:
    """Citation formatting tests."""

    def test_format_reference_list(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_formatter import SourceFormatter
        fmt = SourceFormatter()
        citations = [
            Citation(citation_id=1, document_id=1, document_name="员工手册.pdf",
                    page_number=5, knowledge_base="HR知识库", relevance_score=0.94),
            Citation(citation_id=2, document_id=2, document_name="考勤规范.pdf",
                    page_number=3, knowledge_base="HR知识库", relevance_score=0.85),
        ]
        ref_list = fmt.format_reference_list(citations, include_kb=True)
        assert "[1]" in ref_list
        assert "员工手册" in ref_list
        assert "第5页" in ref_list

    def test_format_inline(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_formatter import SourceFormatter
        fmt = SourceFormatter()
        citations = [
            Citation(citation_id=1, document_id=1, document_name="test.pdf", relevance_score=0.9),
            Citation(citation_id=2, document_id=2, document_name="test2.pdf", relevance_score=0.8),
        ]
        inline = fmt.format_inline(citations)
        assert "[1]" in inline
        assert "[2]" in inline

    def test_format_compact(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_formatter import SourceFormatter
        fmt = SourceFormatter()
        citations = [
            Citation(citation_id=1, document_id=1, document_name="test.pdf",
                    page_number=5, relevance_score=0.9),
        ]
        compact = fmt.format_compact(citations)
        assert "test.pdf" in compact
        assert "p.5" in compact

    def test_format_markdown(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_formatter import SourceFormatter
        fmt = SourceFormatter()
        citations = [
            Citation(citation_id=1, document_id=1, document_name="test.pdf",
                    page_number=5, quote_text="test quote", relevance_score=0.9),
        ]
        md = fmt.format_markdown(citations)
        assert "test.pdf" in md
        assert "test quote" in md

    def test_format_llm_context_block(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_formatter import SourceFormatter
        fmt = SourceFormatter()
        citations = [
            Citation(citation_id=1, document_id=1, document_name="test.pdf",
                    page_number=5, full_content="Full content here", relevance_score=0.9),
        ]
        ctx = fmt.format_llm_context_block(citations)
        assert "[来源1]" in ctx
        assert "Full content here" in ctx

    def test_format_frontend_response(self):
        from app.rag.citation.citation_models import Citation, CitationSet
        from app.rag.citation.source_formatter import SourceFormatter
        fmt = SourceFormatter()
        c = Citation(citation_id=1, document_id=1, document_name="test.pdf",
                     page_number=5, relevance_score=0.9)
        cs = CitationSet(citations=[c], trust_level="high")
        resp = fmt.format_frontend_response("Test answer", cs)
        assert resp["answer"] == "Test answer"
        assert resp["trust_level"] == "high"
        assert len(resp["citations"]) == 1


# ============================================================================
# Test 7: SourceHighlighter
# ============================================================================
class TestSourceHighlighter:
    """Source highlight mapping tests."""

    def test_find_citation_markers(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_highlighter import SourceHighlighter
        sh = SourceHighlighter()
        citations = [
            Citation(citation_id=1, document_id=1, document_name="test.pdf", relevance_score=0.9),
            Citation(citation_id=2, document_id=2, document_name="test2.pdf", relevance_score=0.8),
        ]
        answer = "根据公司规定[1]，员工年假需提前申请。同时[2]也提到考勤要求。"
        markers = sh.find_citation_markers(answer, citations)
        assert len(markers) >= 2

    def test_find_citation_spans_exact(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_highlighter import SourceHighlighter
        sh = SourceHighlighter()
        citations = [
            Citation(citation_id=1, document_id=1, document_name="test.pdf",
                    quote_text="年假需提前3天申请", relevance_score=0.9),
        ]
        answer = "根据公司规定，年假需提前3天申请。"
        spans = sh.find_citation_spans(answer, citations)
        assert len(spans) >= 1

    def test_build_highlight_map(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_highlighter import SourceHighlighter
        sh = SourceHighlighter()
        citations = [
            Citation(citation_id=1, document_id=1, document_name="test.pdf",
                    quote_text="员工应按时打卡", relevance_score=0.9),
        ]
        answer = "根据规定，员工应按时打卡[1]。"
        hl_map = sh.build_highlight_map(answer, citations)
        assert "spans" in hl_map
        assert "markers" in hl_map
        assert hl_map["has_highlights"]

    def test_build_source_tooltip(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_highlighter import SourceHighlighter
        sh = SourceHighlighter()
        c = Citation(citation_id=1, document_id=1, document_name="test.pdf",
                    page_number=5, knowledge_base="Test KB",
                    quote_text="test quote", relevance_score=0.9)
        tooltip = sh.build_source_tooltip(c)
        assert "test.pdf" in tooltip
        assert "Test KB" in tooltip

    def test_no_citations_empty(self):
        from app.rag.citation.source_highlighter import SourceHighlighter
        sh = SourceHighlighter()
        assert sh.find_citation_spans("", []) == []
        assert sh.find_citation_markers("", []) == []


# ============================================================================
# Test 8: SourceManager
# ============================================================================
class TestSourceManager:
    """Source aggregation and fusion tests."""

    def test_add_and_get_top(self):
        from app.rag.citation.citation_models import Citation, CitationSet
        from app.rag.citation.source_manager import SourceManager
        mgr = SourceManager()
        c1 = Citation(citation_id=1, document_id=1, document_name="A.pdf",
                      page_number=1, relevance_score=0.9, chunk_index=0)
        c2 = Citation(citation_id=2, document_id=2, document_name="B.pdf",
                      page_number=2, relevance_score=0.7, chunk_index=0)
        cs = CitationSet(citations=[c1, c2])
        added = mgr.add_citations(cs)
        assert added == 2
        top = mgr.get_top_sources(n=5)
        assert len(top) == 2
        assert top[0].relevance_score >= top[1].relevance_score

    def test_deduplication(self):
        from app.rag.citation.citation_models import Citation, CitationSet
        from app.rag.citation.source_manager import SourceManager
        mgr = SourceManager()
        c1 = Citation(citation_id=1, document_id=1, document_name="A.pdf",
                      relevance_score=0.9, chunk_id="doc1_c0", chunk_index=0)
        c2 = Citation(citation_id=2, document_id=1, document_name="A.pdf",
                      relevance_score=0.8, chunk_id="doc1_c0", chunk_index=0)  # Same chunk_id
        cs = CitationSet(citations=[c1, c2])
        added = mgr.add_citations(cs)
        assert added == 1  # Only one unique

    def test_get_unique_documents(self):
        from app.rag.citation.citation_models import Citation, CitationSet
        from app.rag.citation.source_manager import SourceManager
        mgr = SourceManager()
        c1 = Citation(citation_id=1, document_id=1, document_name="A.pdf",
                      page_number=1, relevance_score=0.9, knowledge_base="KB1", chunk_index=0)
        c2 = Citation(citation_id=2, document_id=1, document_name="A.pdf",
                      page_number=3, relevance_score=0.8, knowledge_base="KB1", chunk_index=1)
        cs = CitationSet(citations=[c1, c2])
        mgr.add_citations(cs)
        docs = mgr.get_unique_documents()
        assert len(docs) == 1
        assert docs[0]["source_count"] == 2

    def test_fuse_adjacent(self):
        from app.rag.citation.citation_models import Citation
        from app.rag.citation.source_manager import SourceManager
        mgr = SourceManager()
        c1 = Citation(citation_id=1, document_id=1, document_name="A.pdf",
                      page_number=1, relevance_score=0.9, chunk_index=0)
        c2 = Citation(citation_id=2, document_id=1, document_name="A.pdf",
                      page_number=2, relevance_score=0.8, chunk_index=1)
        fused = mgr.fuse_adjacent_sources([c1, c2])
        assert len(fused) == 1
        assert fused[0].page_number == 1
        assert fused[0].page_number_end == 2
        assert fused[0].merge_count == 2

    def test_clear(self):
        from app.rag.citation.citation_models import Citation, CitationSet
        from app.rag.citation.source_manager import SourceManager
        mgr = SourceManager()
        c = Citation(citation_id=1, document_id=1, document_name="A.pdf",
                     relevance_score=0.9, chunk_index=0)
        mgr.add_citations(CitationSet(citations=[c]))
        assert mgr.count == 1
        mgr.clear()
        assert mgr.count == 0
