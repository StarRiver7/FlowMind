from fastapi import APIRouter
from src.schemas.rag import RagSearchRequest, RagSearchResponse, RagIndexRequest
from src.rag.retriever import retriever_service

router = APIRouter(prefix="/ai/rag", tags=["RAG"])


@router.post("/search", response_model=RagSearchResponse)
async def search(req: RagSearchRequest):
    chunks = await retriever_service.search(
        query=req.query,
        top_k=req.top_k,
        score_threshold=req.score_threshold,
    )
    return RagSearchResponse(chunks=chunks, total=len(chunks))


@router.post("/index")
async def index_document(req: RagIndexRequest):
    """触发文档索引"""
    # TODO: 完整实现文档加载 -> 分块 -> 向量化 -> 存入Milvus
    return {"status": "accepted", "file_id": req.file_id}
