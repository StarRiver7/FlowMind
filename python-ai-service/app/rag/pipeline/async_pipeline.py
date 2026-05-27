"""Async Pipeline — 异步文档处理 + SSE 实时进度推送.

文档上传后异步触发解析流水线，不阻塞上传接口。
通过 SSE 实时推送处理阶段: 正在解析PDF... → 正在清洗文本... → 正在切分Chunk...
"""

import json
import asyncio
import time
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session

from app.rag.pipeline.document_pipeline import DocumentPipeline
from app.rag.chunk.chunk_strategy import ChunkConfig
from app.core.logger import get_logger

logger = get_logger(__name__)


class AsyncDocumentPipeline:
    """异步文档处理流水线 — SSE 流式进度推送."""

    def __init__(self, chunk_config: Optional[ChunkConfig] = None):
        self._pipeline = DocumentPipeline(chunk_config)

    async def process_async(
        self,
        db: Session,
        document_id: int,
    ) -> dict:
        """异步执行流水线（非 SSE），返回完整结果.

        适用于后台任务触发。
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._pipeline.run,
            db,
            document_id,
        )
        return result

    async def process_with_sse(
        self,
        db: Session,
        document_id: int,
    ) -> AsyncGenerator[str, None]:
        """异步执行 + SSE 实时进度.

        每个阶段推送一个 SSE 事件:
          event: pipeline_progress
          data: {"event":"progress","stage":"parse","status":"running","detail":"正在解析PDF..."}
        """
        start_time = time.time()

        try:
            # 阶段标识
            yield _sse_stage("parse", "running", "正在解析文档...")
            await asyncio.sleep(0.05)

            yield _sse_stage("parse", "running", "识别文档格式，提取文本内容...")
            await asyncio.sleep(0.05)

            # 执行同步流水线（在线程池中）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._pipeline.run,
                db,
                document_id,
            )

            # 从 result 中读取各阶段信息并推送
            stages = result.get("stages", [])
            for stage in stages:
                stage_name = stage.get("stage", "")
                detail = stage.get("detail", "")

                if stage_name == "parse":
                    yield _sse_stage("parse", "completed", f"解析完成: {detail}")
                    yield _sse_stage("clean", "running", "正在清洗文本...")
                    await asyncio.sleep(0.05)

                elif stage_name == "clean":
                    yield _sse_stage("clean", "completed", f"清洗完成: {detail}")
                    yield _sse_stage("chunk", "running", "正在切分Chunk...")
                    await asyncio.sleep(0.05)

                elif stage_name == "chunk":
                    chunk_count = stage.get("chunk_count", 0)
                    yield _sse_stage("chunk", "running", f"正在切分Chunk... 已生成 {chunk_count} 个分块")
                    yield _sse_stage("chunk", "running", "正在统计Token...")
                    await asyncio.sleep(0.05)

                    dk_tokens = stage.get("deepseek_tokens", 0)
                    yield _sse_stage("chunk", "running", f"Token统计: DeepSeek ~{dk_tokens} tokens")
                    yield _sse_stage("chunk", "running", "正在保存Chunk到数据库...")
                    await asyncio.sleep(0.05)

                    qa = stage.get("quality_check", {})
                    qa_status = "通过" if qa.get("passed") else "有警告"
                    yield _sse_stage("chunk", "completed", f"Chunk入库完成 ({chunk_count}个), 质量检查: {qa_status}")

            if result.get("success"):
                summary = result.get("summary", {})
                yield _sse_done(
                    document_id=document_id,
                    chunk_count=summary.get("chunk_count", 0),
                    deepseek_tokens=summary.get("deepseek_tokens", 0),
                    bge_tokens=summary.get("bge_tokens", 0),
                    total_elapsed_ms=summary.get("total_elapsed_ms", 0),
                )
            else:
                yield _sse_error(result.get("error", "处理失败"))

            elapsed = int((time.time() - start_time) * 1000)
            logger.info(
                f"[AsyncPipeline] SSE推送完成 doc_id={document_id} elapsed={elapsed}ms"
            )

        except Exception as e:
            logger.error(f"[AsyncPipeline] 异常 doc_id={document_id}: {e}", exc_info=True)
            yield _sse_error(f"收到老师～文档解析时遇到一点问题，请检查文件格式～")


# ---- SSE 事件构建 ----

def _sse_stage(stage: str, status: str, detail: str) -> str:
    data = json.dumps({
        "event": "progress",
        "stage": stage,
        "status": status,
        "detail": detail,
    }, ensure_ascii=False)
    return f"event: pipeline_progress\ndata: {data}\n\n"


def _sse_done(document_id: int, chunk_count: int, deepseek_tokens: int, bge_tokens: int, total_elapsed_ms: int) -> str:
    data = json.dumps({
        "event": "done",
        "document_id": document_id,
        "chunk_count": chunk_count,
        "deepseek_tokens": deepseek_tokens,
        "bge_tokens": bge_tokens,
        "total_elapsed_ms": total_elapsed_ms,
        "status": "chunked",
    }, ensure_ascii=False)
    return f"event: pipeline_progress\ndata: {data}\n\n"


def _sse_error(message: str) -> str:
    data = json.dumps({"event": "error", "message": message}, ensure_ascii=False)
    return f"event: pipeline_progress\ndata: {data}\n\n"


# 全局单例
async_pipeline = AsyncDocumentPipeline()
