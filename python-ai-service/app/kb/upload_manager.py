"""Upload Manager — 编排上传全流程.

完整链路:
  1. 文件校验 (类型 / 大小 / MIME / 魔数)
  2. 文件落盘 (storage/uploads/{space_id})
  3. 数据库记录 (t_document)
  4. 文档状态跟踪 (UPLOADED)
  5. 通知后续 RAG 处理

支持 SSE 实时推送上传进度。
"""

import json
import time
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session

from app.kb.file_storage import file_storage
from app.kb.document_parser import validate_file, extract_metadata
from app.kb.document_service import document_service
from app.kb.knowledge_base_service import knowledge_base_service
from app.schemas.kb_schemas import UploadResponse
from app.core.logger import get_logger

logger = get_logger(__name__)


class UploadManager:
    """文件上传编排器.

    串联校验 → 存储 → DB 记录 → 状态跟踪的完整链路。
    """

    @staticmethod
    async def upload(
        db: Session,
        space_id: int,
        filename: str,
        content: bytes,
        user_id: int,
        department_id: Optional[int] = None,
    ) -> UploadResponse:
        """执行同步上传（非流式）.

        返回 UploadResponse 包含 document_id 和元信息。

        Raises:
            ValueError: 文件校验失败
            PermissionError: 无权操作该知识空间
        """
        # 1. 权限检查
        space = knowledge_base_service.get_by_id(db, space_id, user_id, department_id)
        if space is None:
            raise PermissionError("知识空间不存在或无权访问")

        # 2. 文件校验
        validation = validate_file(filename, content)
        if not validation.is_valid:
            raise ValueError(validation.error_message or "文件校验失败")

        logger.info(
            f"[Upload] 开始上传 user={user_id} space={space_id} "
            f"file='{filename}' type={validation.file_type} size={validation.file_size}"
        )

        # 3. 去重检查
        existing = document_service.find_by_hash(db, validation.file_hash, space_id)
        if existing:
            raise ValueError(f"文件 '{filename}' 已存在于该知识空间中 (文档ID: {existing.id})")

        # 4. 文件落盘
        file_path, file_hash, file_size = file_storage.save_upload(
            content=content,
            space_id=space_id,
            original_filename=filename,
        )

        # 5. 创建数据库记录
        doc = document_service.create(
            db=db,
            space_id=space_id,
            file_name=filename,
            file_type=validation.file_type.lstrip("."),
            file_size=file_size,
            file_path=file_path,
            file_hash=file_hash,
            creator_id=user_id,
        )

        logger.info(
            f"[Upload] 上传完成 doc_id={doc.id} path='{file_path}' "
            f"status={doc.processing_status}"
        )

        return UploadResponse(
            document_id=doc.id,
            file_name=filename,
            file_type=validation.file_type.lstrip("."),
            file_size=file_size,
            processing_status=doc.processing_status,
            file_hash=file_hash,
            space_id=space_id,
            upload_time=doc.create_time,
        )

    @staticmethod
    async def upload_with_sse(
        db: Session,
        space_id: int,
        filename: str,
        content: bytes,
        user_id: int,
        department_id: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """执行流式上传（SSE），实时推送进度.

        Yields:
            SSE 格式的进度事件字符串。
        """
        try:
            # Step 1: 权限检查
            yield _sse_progress("checking_permission", "正在验证权限...")
            await asyncio.sleep(0.1)

            space = knowledge_base_service.get_by_id(db, space_id, user_id, department_id)
            if space is None:
                yield _sse_error("知识空间不存在或无权访问")
                return

            # Step 2: 文件校验
            yield _sse_progress("validating", "正在校验文件类型与大小...")
            await asyncio.sleep(0.1)

            validation = validate_file(filename, content)
            if not validation.is_valid:
                yield _sse_error(f"收到老师～{validation.error_message}")
                return

            # Step 3: 去重检查
            yield _sse_progress("dedup_check", "正在检查文件是否已存在...")
            existing = document_service.find_by_hash(db, validation.file_hash, space_id)
            if existing:
                yield _sse_error(f"收到老师～文件 '{filename}' 已存在于该知识空间中 (文档ID: {existing.id})")
                return

            # Step 4: 保存文件
            yield _sse_progress("saving", "正在保存文件...")
            file_path, file_hash, file_size = file_storage.save_upload(
                content=content,
                space_id=space_id,
                original_filename=filename,
            )
            await asyncio.sleep(0.1)

            # Step 5: 记录数据库
            yield _sse_progress("recording", "正在记录知识库...")
            doc = document_service.create(
                db=db,
                space_id=space_id,
                file_name=filename,
                file_type=validation.file_type.lstrip("."),
                file_size=file_size,
                file_path=file_path,
                file_hash=file_hash,
                creator_id=user_id,
            )

            # Step 6: 完成
            yield _sse_done(
                document_id=doc.id,
                file_name=filename,
                file_type=validation.file_type.lstrip("."),
                file_size=file_size,
                space_id=space_id,
            )

            logger.info(
                f"[Upload-SSE] 上传完成 doc_id={doc.id} file='{filename}' "
                f"user={user_id} space={space_id}"
            )

        except ValueError as e:
            logger.warning(f"[Upload-SSE] 校验失败: {e}")
            yield _sse_error(f"收到老师～文件上传时遇到一点问题，{str(e)}，请稍后重试～")
        except PermissionError as e:
            logger.warning(f"[Upload-SSE] 权限拒绝: {e}")
            yield _sse_error(f"收到老师～{str(e)}，请检查权限后重试～")
        except Exception as e:
            logger.error(f"[Upload-SSE] 未知错误: {e}", exc_info=True)
            yield _sse_error("收到老师～文件上传时遇到一点问题，请稍后重试～")


# ---- SSE 事件构建 ----

def _sse_progress(step: str, detail: str) -> str:
    data = json.dumps({"event": "progress", "step": step, "detail": detail}, ensure_ascii=False)
    return f"event: upload_progress\ndata: {data}\n\n"


def _sse_error(message: str) -> str:
    data = json.dumps({"event": "error", "message": message}, ensure_ascii=False)
    return f"event: upload_progress\ndata: {data}\n\n"


def _sse_done(document_id: int, file_name: str, file_type: str, file_size: int, space_id: int) -> str:
    data = json.dumps({
        "event": "done",
        "document_id": document_id,
        "file_name": file_name,
        "file_type": file_type,
        "file_size": file_size,
        "space_id": space_id,
    }, ensure_ascii=False)
    return f"event: upload_progress\ndata: {data}\n\n"


# 模块单例
upload_manager = UploadManager()
