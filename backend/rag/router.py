# ============================================================
# rag/router.py — FastAPI RAG Routes
#
# POST /rag/index   → load PDF, chunk, store in Qdrant
# POST /rag/ask     → stream answer using RAG
# GET  /rag/status  → check if a paper is already indexed
# ============================================================

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag.loader import load_and_chunk_pdf, pdf_url_to_collection_name
from rag.vectorstore import collection_exists, create_and_index
from rag.chain import stream_rag_answer

logger = logging.getLogger("gcul_api.rag.router")

router = APIRouter(tags=["rag"])


# ── Request schemas ───────────────────────────────────────────

class IndexRequest(BaseModel):
    pdf_url:    str
    subject:    str
    department: str = ""
    semester:   str = ""


class AskRequest(BaseModel):
    pdf_url:    str
    question:   str
    subject:    str
    department: str = ""
    semester:   str = ""


# ── POST /rag/index ───────────────────────────────────────────

@router.post("/index")
async def index_paper(body: IndexRequest):
    """
    Load a PDF, chunk it, and store embeddings in Qdrant.
    Skips indexing if this paper was already indexed (checks by URL hash).

    Frontend calls this when user opens paper-viewer.html.
    """
    collection = pdf_url_to_collection_name(body.pdf_url)

    # Skip if already indexed — saves time and Qdrant quota
    if collection_exists(collection):
        logger.info("INDEX | Already indexed: %s", collection)
        return {
            "status":     "already_indexed",
            "collection": collection,
            "message":    "Paper already indexed — ready to answer questions.",
        }

    logger.info("INDEX | Indexing: %s  collection=%s", body.subject, collection)

    try:
        chunks = await load_and_chunk_pdf(body.pdf_url)
        create_and_index(collection, chunks)
    except Exception as e:
        logger.exception("INDEX | Failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status":     "indexed",
        "collection": collection,
        "chunks":     len(chunks),
        "message":    f"Indexed {len(chunks)} chunks — ready to answer questions.",
    }


# ── POST /rag/ask ─────────────────────────────────────────────

@router.post("/ask")
async def ask_question(body: AskRequest):
    """
    Stream an answer to a question about a paper using RAG.
    Returns Server-Sent Events (SSE) stream.

    Frontend reads: EventSource or fetch with ReadableStream.
    """
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    collection = pdf_url_to_collection_name(body.pdf_url)

    # Auto-index if not already done
    if not collection_exists(collection):
        logger.info("ASK | Not indexed yet — indexing first: %s", collection)
        try:
            chunks = await load_and_chunk_pdf(body.pdf_url)
            create_and_index(collection, chunks)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

    logger.info(
        "ASK | question='%s…'  collection=%s",
        body.question[:50], collection
    )

    return StreamingResponse(
        stream_rag_answer(
            collection_name=collection,
            question=body.question,
            subject=body.subject,
            department=body.department,
            semester=body.semester,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
        },
    )


# ── GET /rag/status ───────────────────────────────────────────

@router.get("/status")
async def check_status(pdf_url: str):
    """
    Check if a paper is already indexed in Qdrant.
    Frontend calls this to show 'Ready' or 'Indexing…' indicator.
    """
    collection = pdf_url_to_collection_name(pdf_url)
    indexed    = collection_exists(collection)
    return {
        "indexed":    indexed,
        "collection": collection,
    }