"""Chunk Service — Chunk 分块服务编排层.

串联: 策略选择 → 文本分割 → Token 统计 → 元数据构建 → 入库
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.rag.chunk.chunk_strategy import ChunkStrategy, ChunkConfig, ChunkResult
from app.rag.chunk.chunk_metadata import ChunkMetadata, build_chunk_metadata
from app.rag.chunk.token_counter import token_counter, TokenCount
from app.rag.chunk.chunk_storage import chunk_storage
from app.rag.parser.parser_factory import ParsedDocument
from app.core.logger import get_logger

logger = get_logger(__name__)


class ChunkService:
    """Chunk 分块服务.

    接收 ParsedDocument，输出入库的 Chunk 列表及统计信息。
    """

    def __init__(self, config: Optional[ChunkConfig] = None):
        self.strategy = ChunkStrategy(config)

    def process(
        self,
        db: Session,
        parsed_doc: ParsedDocument,
        document_id: int,
    ) -> dict:
        """执行完整的分块流程.

        Steps:
          1. 构建页面位置索引
          2. 执行语义分块
          3. 计算 Token
          4. 构建元数据
          5. 批量入库
          6. 返回统计摘要

        Returns:
            {"chunk_count": N, "total_deepseek_tokens": N, "total_bge_tokens": N, ...}
        """
        start_time = datetime.now()

        # Step 1: 页面位置索引
        pages_index = self._build_page_index(parsed_doc)

        # Step 2: 语义分块
        chunk_results = self.strategy.split(
            text=parsed_doc.full_text,
            title_path=parsed_doc.title_path,
            pages=pages_index,
        )

        if not chunk_results:
            logger.warning(f"[ChunkService] 分块结果为空 doc_id={document_id}")
            return {
                "chunk_count": 0,
                "total_deepseek_tokens": 0,
                "total_bge_tokens": 0,
                "total_chars": 0,
                "elapsed_ms": int((datetime.now() - start_time).total_seconds() * 1000),
            }

        # Step 3: Token 统计
        chunk_texts = [c.content for c in chunk_results]
        token_counts = token_counter.count_batch(chunk_texts)
        total_tokens = token_counter.total_stats(token_counts)

        # Step 4: 构建 ChunkMetadata
        metadata_list: list[ChunkMetadata] = []
        for i, (cr, tc) in enumerate(zip(chunk_results, token_counts)):
            meta = build_chunk_metadata(
                document_id=document_id,
                chunk_index=i,
                content=cr.content,
                token_count=tc.deepseek_tokens,
                page_number=cr.page_number,
                title_path=cr.title_path,
                is_heading_start=cr.is_heading_start,
                overlap_with_prev=cr.overlap_with_prev,
            )
            metadata_list.append(meta)

        # Step 5: 入库
        saved_count = chunk_storage.save_chunks(db, document_id, metadata_list)

        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        result = {
            "chunk_count": saved_count,
            "total_deepseek_tokens": total_tokens.deepseek_tokens,
            "total_bge_tokens": total_tokens.bge_tokens,
            "total_chars": total_tokens.char_count,
            "avg_chunk_size": total_tokens.char_count // max(saved_count, 1),
            "elapsed_ms": elapsed_ms,
        }

        logger.info(
            f"[ChunkService] 分块完成: doc_id={document_id} "
            f"chunks={saved_count} deepseek_tokens={total_tokens.deepseek_tokens} "
            f"bge_tokens={total_tokens.bge_tokens} elapsed={elapsed_ms}ms"
        )

        return result

    def quality_check(self, db: Session, document_id: int) -> dict:
        """对已入库的 Chunk 进行质量检查.

        Returns:
            {"passed": bool, "issues": [...], "summary": str}
        """
        chunks = chunk_storage.get_chunks_by_document(db, document_id)
        issues = []

        if not chunks:
            return {"passed": False, "issues": ["无 Chunk 数据"], "summary": "文档分块后无有效内容"}

        for c in chunks:
            # 空 chunk
            if not c.content or not c.content.strip():
                issues.append(f"chunk #{c.chunk_index}: 空内容")
            # 超长 chunk (>2000 chars)
            if c.char_count > 2000:
                issues.append(f"chunk #{c.chunk_index}: 过长 ({c.char_count} chars)")
            # Token 超限 (>1000 deepseek tokens)
            if c.char_count > 4000:  # rough estimate
                issues.append(f"chunk #{c.chunk_index}: 可能超 Token 限制")

        # 重复检测
        seen = set()
        for c in chunks:
            key = c.content[:100]
            if key in seen:
                issues.append(f"chunk #{c.chunk_index}: 疑似重复内容")
            seen.add(key)

        passed = len(issues) == 0
        summary = "所有 Chunk 通过质量检查" if passed else f"发现 {len(issues)} 个问题"

        return {"passed": passed, "issues": issues, "summary": summary}

    @staticmethod
    def _build_page_index(parsed_doc: ParsedDocument) -> list[dict]:
        """构建页面字符位置索引."""
        index = []
        offset = 0
        for page in parsed_doc.pages:
            page_len = len(page.text)
            index.append({
                "page_number": page.page_number,
                "char_start": offset,
                "char_end": offset + page_len,
            })
            offset += page_len + 2  # +2 for "\n\n" separator
        return index


# 默认实例
chunk_service = ChunkService()
