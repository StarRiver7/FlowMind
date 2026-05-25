# ============================================================
# rerank/base.py — Rerank Layer Abstract
# ============================================================
"""Rerank Layer — post-retrieval relevance scoring.

After initial retrieval, the Rerank layer re-scores results
using a more accurate (but more expensive) model.

Provides:
    - RerankRequest: input for reranking
    - RerankResult: reranked output
    - BaseReranker: abstract interface for any reranking model
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RerankRequest:
    """Input for a reranking operation."""
    query: str
    documents: list[str]
    top_n: int = 5
    return_documents: bool = True


@dataclass
class RerankResult:
    """Single reranked document with score."""
    index: int
    score: float
    document: Optional[str] = None


class BaseReranker(ABC):
    """Abstract contract for relevance reranking models.

    Implementations:
        - CrossEncoderReranker (BGE-Reranker-v2-m3)
        - LLMReranker (GPT-4 based relevance scoring)
        - CohereReranker (Cohere API)
    """

    @abstractmethod
    async def rerank(self, request: RerankRequest) -> list[RerankResult]:
        """Rerank documents by relevance to query.

        Returns results sorted by descending score.
        """
        ...

    @abstractmethod
    async def batch_rerank(
        self,
        requests: list[RerankRequest],
    ) -> list[list[RerankResult]]:
        """Rerank multiple query-document sets in parallel."""
        ...
