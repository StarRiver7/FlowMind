"""Knowledge Base API — 企业知识库上传与管理接口.

Endpoints:
  POST   /api/kb/create          — 创建知识空间
  GET    /api/kb/list            — 列出知识空间
  GET    /api/kb/{space_id}       — 知识空间详情
  PUT    /api/kb/{space_id}       — 更新知识空间
  DELETE /api/kb/{space_id}       — 删除知识空间
  POST   /api/kb/upload           — 上传文档
  POST   /api/kb/upload/stream    — 上传文档 (SSE 实时进度)
  GET    /api/kb/{space_id}/documents  — 知识空间下的文档列表
  GET    /api/kb/document/{doc_id}     — 文档详情
  GET    /api/kb/document/{doc_id}/status — 文档状态
  DELETE /api/kb/document/{doc_id}      — 删除文档
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Request, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.kb.knowledge_base_service import knowledge_base_service
from app.kb.document_service import document_service
from app.kb.upload_manager import upload_manager
from app.schemas.kb_schemas import (
    CreateKnowledgeBaseRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    DocumentResponse,
    DocumentListResponse,
    UploadResponse,
    DocumentStatusResponse,
)
from app.common.response.common import ApiResponse, ErrorResponse
from app.rag.pipeline.document_pipeline import document_pipeline
from app.rag.pipeline.async_pipeline import async_pipeline
from app.rag.chunk.chunk_storage import chunk_storage
from app.rag.chunk.chunk_service import chunk_service
from app.rag.retrieval.retriever import retriever, RetrievalResult
from app.rag.retrieval.hybrid_search import hybrid_search
from app.rag.vector_store.vector_repository import vector_repository
from app.rag.vector_store.milvus_client import milvus_client

from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base - 知识库"])


# ============================================================
# 辅助依赖: 从请求中解析用户上下文
# ============================================================

def _get_current_user_id(request: Request) -> int:
    """从 Header 中获取当前用户 ID（对齐 Java 服务转发）."""
    uid = request.headers.get("X-User-Id", "1")
    return int(uid)


def _get_current_department_id(request: Request) -> Optional[int]:
    """从 Header 获取当前用户部门 ID."""
    did = request.headers.get("X-Department-Id")
    return int(did) if did else None


# ============================================================
# Knowledge Space endpoints
# ============================================================

@router.post("/create", response_model=ApiResponse)
async def create_knowledge_base(
    req: CreateKnowledgeBaseRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """创建知识空间."""
    try:
        user_id = _get_current_user_id(request)
        space = knowledge_base_service.create(db, req, user_id)
        return ApiResponse(
            message="知识空间创建成功",
            data=KnowledgeBaseResponse.model_validate(space).model_dump(),
        ).model_dump()
    except ValueError as e:
        return ErrorResponse(code=400, message=str(e)).model_dump()
    except Exception as e:
        logger.error(f"[KB-API] 创建知识空间失败: {e}", exc_info=True)
        return ErrorResponse(code=500, message="收到老师～创建知识空间时遇到一点问题，请稍后重试～").model_dump()


@router.get("/list", response_model=ApiResponse)
async def list_knowledge_bases(
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """列出用户有权限的知识空间."""
    try:
        user_id = _get_current_user_id(request)
        department_id = _get_current_department_id(request)
        items, total = knowledge_base_service.list_for_user(db, user_id, department_id, offset, limit)
        return ApiResponse(
            data=KnowledgeBaseListResponse(
                items=[KnowledgeBaseResponse.model_validate(s) for s in items],
                total=total,
            ).model_dump(),
        ).model_dump()
    except Exception as e:
        logger.error(f"[KB-API] 列出知识空间失败: {e}", exc_info=True)
        return ErrorResponse(code=500, message="收到老师～获取知识空间列表时遇到一点问题，请稍后重试～").model_dump()


@router.get("/{space_id}", response_model=ApiResponse)
async def get_knowledge_base(
    space_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """获取知识空间详情."""
    user_id = _get_current_user_id(request)
    department_id = _get_current_department_id(request)
    space = knowledge_base_service.get_by_id(db, space_id, user_id, department_id)
    if not space:
        return ErrorResponse(code=404, message="知识空间不存在或无权访问").model_dump()
    return ApiResponse(data=KnowledgeBaseResponse.model_validate(space).model_dump()).model_dump()


@router.put("/{space_id}", response_model=ApiResponse)
async def update_knowledge_base(
    space_id: int,
    req: CreateKnowledgeBaseRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """更新知识空间（仅创建者可操作）."""
    user_id = _get_current_user_id(request)
    department_id = _get_current_department_id(request)
    space = knowledge_base_service.update(
        db, space_id, user_id, department_id,
        **req.model_dump(exclude_none=True),
    )
    if not space:
        return ErrorResponse(code=404, message="知识空间不存在或无权修改").model_dump()
    return ApiResponse(
        message="知识空间更新成功",
        data=KnowledgeBaseResponse.model_validate(space).model_dump(),
    ).model_dump()


@router.delete("/{space_id}", response_model=ApiResponse)
async def delete_knowledge_base(
    space_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """删除知识空间（仅创建者可操作）."""
    user_id = _get_current_user_id(request)
    department_id = _get_current_department_id(request)
    ok = knowledge_base_service.delete(db, space_id, user_id, department_id)
    if not ok:
        return ErrorResponse(code=404, message="知识空间不存在或无权删除").model_dump()
    return ApiResponse(message="知识空间已删除").model_dump()


# ============================================================
# Document Upload endpoints
# ============================================================

@router.post("/upload", response_model=ApiResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    space_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """上传文档到指定知识空间.

    支持 multipart/form-data，返回文档元信息。
    """
    try:
        user_id = _get_current_user_id(request)
        department_id = _get_current_department_id(request)

        content = await file.read()

        result = await upload_manager.upload(
            db=db,
            space_id=space_id,
            filename=file.filename or "unknown",
            content=content,
            user_id=user_id,
            department_id=department_id,
        )

        return ApiResponse(
            message="文档上传成功",
            data=result.model_dump(),
        ).model_dump()

    except ValueError as e:
        logger.warning(f"[KB-API] 上传校验失败: {e}")
        return ErrorResponse(
            code=400,
            message=f"收到老师～文件上传时遇到一点问题，{str(e)}，请稍后重试～",
        ).model_dump()
    except PermissionError as e:
        logger.warning(f"[KB-API] 上传权限拒绝: {e}")
        return ErrorResponse(code=403, message=str(e)).model_dump()
    except Exception as e:
        logger.error(f"[KB-API] 上传未知错误: {e}", exc_info=True)
        return ErrorResponse(
            code=500,
            message="收到老师～文件上传时遇到一点问题，请稍后重试～",
        ).model_dump()


@router.post("/upload/stream")
async def upload_document_stream(
    request: Request,
    file: UploadFile = File(...),
    space_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """上传文档 (SSE 流式进度推送)."""
    user_id = _get_current_user_id(request)
    department_id = _get_current_department_id(request)

    content = await file.read()

    return StreamingResponse(
        upload_manager.upload_with_sse(
            db=db,
            space_id=space_id,
            filename=file.filename or "unknown",
            content=content,
            user_id=user_id,
            department_id=department_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


# ============================================================
# Document Management endpoints
# ============================================================

@router.get("/{space_id}/documents", response_model=ApiResponse)
async def list_documents(
    space_id: int,
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """列出知识空间下的文档列表."""
    user_id = _get_current_user_id(request)
    department_id = _get_current_department_id(request)

    # 权限校验
    space = knowledge_base_service.get_by_id(db, space_id, user_id, department_id)
    if not space:
        return ErrorResponse(code=404, message="知识空间不存在或无权访问").model_dump()

    items, total = document_service.list_by_space(db, space_id, offset, limit, status)
    return ApiResponse(
        data=DocumentListResponse(
            items=[DocumentResponse.model_validate(d) for d in items],
            total=total,
        ).model_dump(),
    ).model_dump()


@router.get("/document/{doc_id}", response_model=ApiResponse)
async def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
):
    """获取文档详情."""
    doc = document_service.get_by_id(db, doc_id)
    if not doc:
        return ErrorResponse(code=404, message="文档不存在").model_dump()
    return ApiResponse(data=DocumentResponse.model_validate(doc).model_dump()).model_dump()


@router.get("/document/{doc_id}/status", response_model=ApiResponse)
async def get_document_status(
    doc_id: int,
    db: Session = Depends(get_db),
):
    """获取文档处理状态."""
    doc = document_service.get_by_id(db, doc_id)
    if not doc:
        return ErrorResponse(code=404, message="文档不存在").model_dump()
    return ApiResponse(
        data=DocumentStatusResponse(
            document_id=doc.id,
            processing_status=doc.processing_status,
            chunk_count=doc.chunk_count,
            token_count=doc.token_count,
            error_msg=doc.error_msg,
        ).model_dump(),
    ).model_dump()


@router.delete("/document/{doc_id}", response_model=ApiResponse)
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
):
    """删除文档."""
    doc = document_service.get_by_id(db, doc_id)
    if not doc:
        return ErrorResponse(code=404, message="文档不存在").model_dump()

    ok = document_service.soft_delete(db, doc_id)
    if not ok:
        return ErrorResponse(code=500, message="删除文档失败").model_dump()

    return ApiResponse(message="文档已删除").model_dump()

# ============================================================
# Document Processing endpoints
# ============================================================

@router.post("/document/{doc_id}/parse", response_model=ApiResponse)
async def parse_document(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """触发文档解析流水线 (同步).

    执行: Parse → Clean → Chunk → Store
    返回详细的阶段报告。
    """
    try:
        result = document_pipeline.run(db, doc_id)
        if result["success"]:
            return ApiResponse(
                message="文档解析完成",
                data=result,
            ).model_dump()
        else:
            return ErrorResponse(
                code=400,
                message=result.get("error", "文档解析失败"),
                detail=str(result.get("summary", {})),
            ).model_dump()
    except Exception as e:
        logger.error(f"[KB-API] 解析文档失败 doc_id={doc_id}: {e}", exc_info=True)
        return ErrorResponse(
            code=500,
            message="收到老师～文档解析时遇到一点问题，请稍后重试～",
        ).model_dump()


@router.post("/document/{doc_id}/parse/stream")
async def parse_document_stream(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """触发文档解析流水线 (SSE 流式进度推送)."""
    return StreamingResponse(
        async_pipeline.process_with_sse(db, doc_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


@router.get("/document/{doc_id}/chunks", response_model=ApiResponse)
async def get_document_chunks(
    doc_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """获取文档的所有 Chunk."""
    chunks = chunk_storage.get_chunks_by_document(db, doc_id, offset, limit)
    total = chunk_storage.get_chunk_count(db, doc_id)
    return ApiResponse(
        data={
            "chunks": [
                {
                    "id": c.id,
                    "chunk_index": c.chunk_index,
                    "content": c.content,
                    "char_count": c.char_count,
                    "page_number": c.page_number,
                    "is_embedded": c.is_embedded,
                    "create_time": c.create_time.isoformat() if c.create_time else None,
                }
                for c in chunks
            ],
            "total": total,
        },
    ).model_dump()


@router.get("/document/{doc_id}/quality", response_model=ApiResponse)
async def check_document_quality(
    doc_id: int,
    db: Session = Depends(get_db),
):
    """检查文档 Chunk 质量."""
    result = chunk_service.quality_check(db, doc_id)
    return ApiResponse(data=result).model_dump()



# ============================================================
# Retrieval / Search endpoints
# ============================================================

@router.post("/search", response_model=ApiResponse)
async def search_knowledge_base(
    request: Request,
    query: str = Form(...),
    top_k: int = Form(default=5),
    space_id: Optional[int] = Form(default=None),
    db: Session = Depends(get_db),
):
    """Search knowledge base with hybrid retrieval."""
    try:
        user_id = _get_current_user_id(request)
        department_id = _get_current_department_id(request)
        space_ids = [space_id] if space_id else None

        result = await retriever.retrieve(
            query=query,
            top_k=top_k * 2,
            final_k=top_k,
            user_id=user_id,
            department_id=department_id,
            space_ids=space_ids,
            build_context=True,
        )

        return ApiResponse(
            message="search completed",
            data={
                "query": result.query,
                "chunks": result.chunks,
                "sources": result.sources,
                "context_text": result.context_text,
                "total_chunks": result.total_chunks,
                "total_chars": result.total_chars,
                "elapsed_ms": result.elapsed_ms,
                "truncated": result.truncated,
            },
        ).model_dump()
    except Exception as e:
        logger.error(f"[KB-API] search error: {e}", exc_info=True)
        return ErrorResponse(code=500, message="search failed").model_dump()


@router.post("/document/{doc_id}/index", response_model=ApiResponse)
async def index_document(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Index document chunks into Milvus."""
    try:
        result = await vector_repository.index_document(db, doc_id)
        if result.get("success"):
            return ApiResponse(message="index complete", data=result).model_dump()
        else:
            return ErrorResponse(code=400, message=result.get("error", "index failed")).model_dump()
    except Exception as e:
        logger.error(f"[KB-API] index error doc_id={doc_id}: {e}", exc_info=True)
        return ErrorResponse(code=500, message="index failed, please retry").model_dump()


@router.get("/milvus/stats", response_model=ApiResponse)
async def get_milvus_stats():
    """Get Milvus collection stats."""
    try:
        count = milvus_client.count()
        return ApiResponse(data={"total_vectors": count}).model_dump()
    except Exception as e:
        return ErrorResponse(code=500, message=str(e)).model_dump()
