"""Metadata Boost — boost retrieval scores based on metadata signals.

Boost factors:
  1. Title/heading chunks (+0.05 per heading level match)
  2. Recent documents (+0.03 for docs < 30 days old)
  3. Department match (+0.05 for same department)
  4. Higher chunk count docs (more comprehensive, +0.02)

All boosts are additive and capped at 1.0.
"""

import time
from datetime import datetime, timedelta
from typing import Optional
from app.core.logger import get_logger

logger = get_logger(__name__)


class MetadataBoost:
    """Apply score boosts based on chunk metadata."""

    def __init__(self):
        self._boost_config = {
            "title_match": 0.05,
            "recent_doc": 0.03,
            "department_match": 0.05,
            "high_quality": 0.02,
            "max_total_boost": 0.15,
        }

    def apply(
        self,
        chunks: list[dict],
        *,
        query: str = "",
        department_id: Optional[int] = None,
        recent_days: int = 30,
    ) -> list[dict]:
        """Apply metadata boosts to retrieval results.

        Args:
            chunks: retrieval results with scores
            query: original query (for title matching)
            department_id: user's department for department boost
            recent_days: number of days considered "recent"

        Returns:
            Chunks with boosted scores (original score preserved as raw_score).
        """
        now_ms = int(time.time() * 1000)
        recent_cutoff = now_ms - (recent_days * 86400 * 1000)

        for c in chunks:
            original_score = c.get("score", 0)
            total_boost = 0.0

            # 1. Title/heading boost
            title_path = c.get("title_path", "")
            if title_path and query:
                query_terms = set(query.lower().split())
                title_terms = set(title_path.lower().split())
                if query_terms & title_terms:
                    total_boost += self._boost_config["title_match"]

            # 2. Recent document boost
            created_time = c.get("created_time", 0)
            if created_time and created_time > recent_cutoff:
                total_boost += self._boost_config["recent_doc"]

            # 3. Department match boost
            chunk_dept = c.get("department_id")
            if department_id is not None and chunk_dept == department_id:
                total_boost += self._boost_config["department_match"]

            # 4. Cap boost
            total_boost = min(total_boost, self._boost_config["max_total_boost"])

            c["raw_score"] = original_score
            c["score"] = min(1.0, original_score + total_boost)
            c["metadata_boost"] = total_boost

        # Re-sort
        chunks.sort(key=lambda x: x["score"], reverse=True)
        return chunks


metadata_boost = MetadataBoost()
