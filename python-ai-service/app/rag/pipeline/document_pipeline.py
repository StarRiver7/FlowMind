"""Document Pipeline — 文档解析→清洗→分块→入库 完整流水线.

流程:
    t_document (status=uploaded)
        ↓
    [1] ParserFactory.parse()       → ParsedDocument
        ↓  status → parsing
    [2] TextCleaner.clean()         → cleaned text + CleaningReport
        ↓  status → parsed
    [3] ChunkService.process()      → chunks saved to t_document_chunk
        ↓  status → chunking → chunked
    [4] Update t_document stats     → chunk_count, token_count
"""

import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.rag.parser.parser_factory import parser_factory
from app.rag.parser.pdf_parser import PdfParser
from app.rag.parser.docx_parser import DocxParser
from app.rag.parser.md_parser import MdParser
from app.rag.parser.txt_parser import TxtParser
from app.rag.parser.text_cleaner import text_cleaner, CleaningReport
from app.rag.chunk.chunk_service import chunk_service
from app.rag.vector_store.vector_repository import vector_repository
from app.rag.chunk.chunk_strategy import ChunkConfig
from app.kb.file_storage import file_storage
from app.kb.document_service import document_service
from app.kb.document_status import DocumentStatus
from app.kb.models import Document
from app.core.logger import get_logger

logger = get_logger(__name__)


# 注册所有解析器（模块加载时自动执行）
_parsers_registered = False


def _register_parsers():
    global _parsers_registered
    if _parsers_registered:
        return
    parser_factory.register(PdfParser())
    parser_factory.register(DocxParser())
    parser_factory.register(MdParser())
    parser_factory.register(TxtParser())
    _parsers_registered = True


class DocumentPipeline:
    """文档处理流水线 — 编排 parse → clean → chunk → store.

    使用方法:
        pipeline = DocumentPipeline()
        result = pipeline.run(db, document_id)
    """

    def __init__(self, chunk_config: Optional[ChunkConfig] = None):
        _register_parsers()
        self.chunk_config = chunk_config or ChunkConfig()

    def run(self, db: Session, document_id: int) -> dict:
        """执行完整的文档处理流水线.

        串行执行: Parse → Clean → Chunk → Store → Update Status.
        每个阶段的耗时和结果都会记录。

        Args:
            db: 数据库会话
            document_id: t_document.id

        Returns:
            {
                "success": True/False,
                "document_id": int,
                "stages": [{stage, status, elapsed_ms}, ...],
                "summary": {...},
                "error": str | None,
            }
        """
        start_total = time.time()
        stages = []
        summary = {}
        error_msg = None

        # 获取文档记录
        doc = document_service.get_by_id(db, document_id)
        if not doc:
            return {"success": False, "document_id": document_id, "error": "文档不存在"}

        file_name = doc.file_name
        file_type = doc.file_type
        rel_path = doc.file_path

        logger.info(
            f"[Pipeline] 开始处理 doc_id={document_id} "
            f"file='{file_name}' type={file_type} status={doc.processing_status}"
        )

        try:
            # ── Stage 1: Parse ──
            stage_start = time.time()
            document_service.update_status(db, document_id, DocumentStatus.PARSING)
            db.commit()

            file_content = file_storage.read_file(rel_path)
            parsed_doc = parser_factory.parse(
                file_path=rel_path,
                file_name=file_name,
                content=file_content,
                file_type=file_type,
            )

            if parsed_doc.parse_errors and not parsed_doc.full_text:
                raise ValueError(f"文档解析失败: {'; '.join(parsed_doc.parse_errors)}")

            document_service.update_status(db, document_id, DocumentStatus.PARSED)
            db.commit()

            parse_elapsed = int((time.time() - stage_start) * 1000)
            stages.append({
                "stage": "parse",
                "status": "completed",
                "elapsed_ms": parse_elapsed,
                "detail": f"解析完成: {parsed_doc.total_pages}页, {parsed_doc.total_chars}字符",
                "parser": parsed_doc.metadata.get("parser", "unknown"),
            })
            logger.info(f"[Pipeline] Stage 1 Parse: {parse_elapsed}ms, {parsed_doc.total_chars} chars")

            # ── Stage 2: Clean ──
            stage_start = time.time()
            cleaned_text, clean_report = text_cleaner.clean(parsed_doc.full_text)
            parsed_doc.full_text = cleaned_text  # 更新为清洗后的文本

            clean_elapsed = int((time.time() - stage_start) * 1000)
            stages.append({
                "stage": "clean",
                "status": "completed",
                "elapsed_ms": clean_elapsed,
                "detail": (
                    f"清洗完成: {clean_report.original_chars}→{clean_report.cleaned_chars}字符 "
                    f"(-{clean_report.removed_chars})"
                ),
                "cleaning_report": {
                    "removed_chars": clean_report.removed_chars,
                    "blank_lines_removed": clean_report.blank_lines_removed,
                    "html_tags_removed": clean_report.html_tags_removed,
                    "steps": clean_report.steps_applied,
                },
            })
            logger.info(f"[Pipeline] Stage 2 Clean: {clean_elapsed}ms")

            # ── Stage 3: Chunk ──
            stage_start = time.time()
            document_service.update_status(db, document_id, DocumentStatus.CHUNKING)
            db.commit()

            chunk_result = chunk_service.process(db, parsed_doc, document_id)
            if chunk_result["chunk_count"] == 0:
                raise ValueError("文档分块后无有效内容，请检查文档是否为空")

            # 质量检查
            qa_result = chunk_service.quality_check(db, document_id)

            chunk_elapsed = int((time.time() - stage_start) * 1000)
            stages.append({
                "stage": "chunk",
                "status": "completed",
                "elapsed_ms": chunk_elapsed,
                "chunk_count": chunk_result["chunk_count"],
                "deepseek_tokens": chunk_result["total_deepseek_tokens"],
                "bge_tokens": chunk_result["total_bge_tokens"],
                "avg_chunk_size": chunk_result["avg_chunk_size"],
                "quality_check": qa_result,
            })
            logger.info(
                f"[Pipeline] Stage 3 Chunk: {chunk_elapsed}ms, "
                f"{chunk_result['chunk_count']} chunks, "
                f"quality={'PASS' if qa_result['passed'] else 'ISSUES'}"
            )

            # ---- Stage 4: Embedding + Milvus Index ----
            stage_start = time.time()
            document_service.update_status(db, document_id, DocumentStatus.EMBEDDING)
            db.commit()
            

            import asyncio
            loop = asyncio.new_event_loop()
            index_result = loop.run_until_complete(
                vector_repository.index_document(db, document_id)
            )
            loop.close()

            if not index_result.get("success"):
                raise ValueError(index_result.get("error", "vector index failed"))

            embed_elapsed = int((time.time() - stage_start) * 1000)
            stages.append({
                "stage": "embedding",
                "status": "completed",
                "elapsed_ms": embed_elapsed,
                "vector_count": index_result.get("vector_count", 0),
                "detail": f"vector index: {index_result.get('vector_count', 0)} vectors",
            })
            logger.info(f"[Pipeline] Stage 4 Embedding: {embed_elapsed}ms")

            # ---- Stage 5: Final Status ----
            document_service.update_status(
                db, document_id,
                new_status=DocumentStatus.CHUNKED,
                chunk_count=chunk_result["chunk_count"],
                token_count=chunk_result["total_deepseek_tokens"],
            )
            db.commit()

            total_elapsed = int((time.time() - start_total) * 1000)
            summary = {
                "document_id": document_id,
                "file_name": file_name,
                "file_type": file_type,
                "total_chars": parsed_doc.total_chars,
                "cleaned_chars": clean_report.cleaned_chars,
                "chunk_count": chunk_result["chunk_count"],
                "deepseek_tokens": chunk_result["total_deepseek_tokens"],
                "bge_tokens": chunk_result["total_bge_tokens"],
                "total_elapsed_ms": total_elapsed,
                "status": "chunked",
            }

            logger.info(
                f"[Pipeline] 处理完成 doc_id={document_id}: "
                f"{chunk_result['chunk_count']} chunks, {total_elapsed}ms total"
            )

            return {
                "success": True,
                "document_id": document_id,
                "stages": stages,
                "summary": summary,
                "error": None,
            }

        except Exception as e:
            error_msg = f"收到老师～文档解析时遇到一点问题，{str(e)[:200]}，请检查文件格式～"
            logger.error(f"[Pipeline] 处理失败 doc_id={document_id}: {e}", exc_info=True)
            document_service.mark_failed(db, document_id, str(e)[:1000])
            db.commit()

            total_elapsed = int((time.time() - start_total) * 1000)
            return {
                "success": False,
                "document_id": document_id,
                "stages": stages,
                "summary": {"total_elapsed_ms": total_elapsed},
                "error": error_msg,
            }


# 全局单例
document_pipeline = DocumentPipeline()
