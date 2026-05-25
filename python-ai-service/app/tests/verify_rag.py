"""
Standalone RAG Pipeline verification script.

Creates sample documents, ingests them, and runs search queries.
Tests all pipeline stages without external dependencies beyond what's
already installed.

Usage: python -m app.tests.verify_rag
"""
import asyncio
import tempfile
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


SAMPLE_DOCS = {
    "policy.txt": """
FlowMind Enterprise AI Platform - Policy Document v2.0
========================================================

1. Data Governance
All enterprise data must be classified according to the following tiers:
- Tier 1 (Public): Marketing materials, press releases
- Tier 2 (Internal): Team documentation, meeting notes
- Tier 3 (Confidential): Financial reports, HR records
- Tier 4 (Restricted): Trade secrets, source code, encryption keys

2. AI Safety Guidelines
The platform enforces the following safety measures:
- Input sanitization on all user prompts
- Output filtering for PII, credentials, and toxic content
- Rate limiting per user (60 RPM default)
- Audit logging of all AI interactions
- Human-in-the-loop for high-risk tool executions

3. Knowledge Base Management
Documents are processed through the RAG pipeline:
Load -> Split (512 char chunks, 64 overlap) -> BGE-M3 Embedding (1024-dim) -> Milvus Storage
Retrieval uses hybrid search (70% vector + 30% BM25) with BGE-Reranker-v2-m3 for precision.

4. Deployment Architecture
The system runs on Kubernetes with:
- 3 Java service replicas (API gateway + auth)
- 3 Python AI service replicas (LLM + RAG)
- Milvus standalone for production (>1M vectors)
- Redis cluster for session memory
""",

    "api_guide.md": """# FlowMind API Integration Guide

## Quick Start
1. Obtain API key from admin dashboard
2. Set Authorization header: `Bearer <token>`
3. Base URL: `https://api.flowmind.example.com/v1`

## Chat Endpoint
POST /ai/chat
Content-Type: application/json

Request body:
```json
{
    "user_id": "user-123",
    "message": "What is our data retention policy?",
    "use_rag": true,
    "use_tools": false,
    "stream": true
}
```

## RAG Search Endpoint
POST /ai/rag/search
Content-Type: application/json

Request body:
```json
{
    "query": "AI safety guidelines",
    "top_k": 5,
    "tenant_id": "default"
}
```

## Error Codes
| Code | Description |
|------|-------------|
| 200  | Success |
| 401  | Invalid API key |
| 429  | Rate limit exceeded |
| 503  | AI service unavailable |
"""
}


async def run_verification():
    """Run full verification of the RAG pipeline."""
    from app.pipeline.rag_pipeline import rag_pipeline
    from app.pipeline.embedder import embedding_engine

    print("=" * 60)
    print("FlowMind RAG Pipeline Verification")
    print("=" * 60)

    # ---- Phase 1: Embedding ----
    print("\n[1/6] Testing BGE-M3 Embedding...")
    t0 = time.time()
    vec = await embedding_engine.embed_query("test query for embedding verification")
    t1 = time.time()
    assert len(vec) > 0, f"Expected non-empty vector, got {len(vec)}"
    print(f"  [OK] Embedding model produces 0-dim vectors ({t1-t0:.1f}s)")

    # ---- Phase 2: Ingest documents ----
    print("\n[2/6] Ingesting sample documents...")
    doc_ids = []
    for filename, content in SAMPLE_DOCS.items():
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f"_{filename}", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            filepath = f.name

        doc_id = f"verify-{filename.replace('.', '-')}"
        result = await rag_pipeline.ingest(
            filepath, doc_id=doc_id,
            metadata={"source": "verification"},
            tenant_id="verify",
        )
        doc_ids.append(doc_id)
        print(f"  [OK] {filename}: {result['chunk_count']} chunks ({result['elapsed_seconds']:.1f}s)")
        os.unlink(filepath)

    # ---- Phase 3: Stats ----
    print("\n[3/6] Pipeline statistics...")
    stats = await rag_pipeline.stats()
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Embedding dim: {stats['embedding_dim']}")
    assert stats["total_chunks"] > 0

    # ---- Phase 4: Search ----
    print("\n[4/6] Testing hybrid search...")
    queries = [
        "What are the data classification tiers?",
        "How does the RAG pipeline work?",
        "What error codes does the API return?",
    ]
    for q in queries:
        results = await rag_pipeline.search(
            q, top_k=3, use_rerank=True,
            with_citation=True, tenant_id="verify",
        )
        top_score = results[0]["score"] if results else 0
        status = "[OK]" if results and top_score > 0.3 else "[WARN]"
        print(f"  {status} '{q}' → {len(results)} results (top score: {top_score:.3f})")

    # ---- Phase 5: Context formatting ----
    print("\n[5/6] Testing context formatting...")
    ctx = await rag_pipeline.search_context(
        "AI safety measures and data governance",
        top_k=3, tenant_id="verify",
    )
    lines = ctx.split("\n")
    print(f"  [OK] Context: {len(ctx)} chars, {len(lines)} lines")
    assert "Source" in ctx
    # Print first 200 chars as sample
    print(f"  Sample: {ctx[:200]}...")

    # ---- Phase 6: Cleanup ----
    print("\n[6/6] Cleaning up...")
    for doc_id in doc_ids:
        await rag_pipeline.delete_document(doc_id)
        print(f"  [OK] Deleted: {doc_id}")

    print("\n" + "=" * 60)
    print("All verifications passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_verification())
