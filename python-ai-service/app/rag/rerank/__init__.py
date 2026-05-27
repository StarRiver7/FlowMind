"""Rerank module — semantic re-ranking for enterprise RAG.

Pipeline:
  TopK → CrossEncoder → CompositeScore → DuplicateFilter → TopN

Key components:
  - CrossEncoder: pairwise (query, chunk) relevance scoring
  - RerankPipeline: full orchestration
  - RerankScorer: composite score calculation
  - DuplicateFilter: near-duplicate removal
"""

from app.rag.rerank.reranker import reranker, Reranker
from app.rag.rerank.cross_encoder import cross_encoder, CrossEncoder
from app.rag.rerank.rerank_pipeline import rerank_pipeline, RerankPipeline
from app.rag.rerank.rerank_score import rerank_scorer, RerankScorer, ScoreConfig
from app.rag.rerank.duplicate_filter import duplicate_filter, DuplicateFilter
