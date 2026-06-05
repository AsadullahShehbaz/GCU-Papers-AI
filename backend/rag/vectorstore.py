# ============================================================
# rag/vectorstore.py — Qdrant Vector Store Operations
# Handles: collection creation, upsert, similarity search
# ============================================================

import logging
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from config import settings

logger = logging.getLogger("gcul_api.rag.vectorstore")

# ── Embedding model ───────────────────────────────────────────
# Free, runs locally — no API key needed
# 384-dimensional vectors, fast and accurate for Q&A
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE     = 384

# Lazy-loaded singleton so model loads once at startup
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        logger.info("VECTORSTORE | Loading embedding model: %s", EMBEDDING_MODEL)
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("VECTORSTORE | Embedding model loaded ✓")
    return _embeddings


def get_qdrant_client() -> QdrantClient:
    """Create Qdrant Cloud client using env vars."""
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )


def collection_exists(collection_name: str) -> bool:
    """Check if a Qdrant collection already exists."""
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    exists = collection_name in existing
    logger.info(
        "VECTORSTORE | Collection '%s' exists: %s", collection_name, exists
    )
    return exists


def create_and_index(collection_name: str, chunks: list) -> QdrantVectorStore:
    """
    Create a new Qdrant collection and index all chunks.

    Args:
        collection_name: unique name for this paper
        chunks: list of LangChain Document objects

    Returns:
        QdrantVectorStore instance ready for similarity search
    """
    client = get_qdrant_client()

    # Create collection with cosine similarity
    logger.info("VECTORSTORE | Creating collection: %s", collection_name)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

    # Index chunks
    logger.info("VECTORSTORE | Indexing %d chunks…", len(chunks))
    vectorstore = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=collection_name,
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

    logger.info("VECTORSTORE | Indexed ✓  collection=%s", collection_name)
    return vectorstore


def get_vectorstore(collection_name: str) -> QdrantVectorStore:
    """
    Get existing Qdrant collection as a vectorstore.
    Call this when collection already exists.
    """
    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=collection_name,
        embedding=get_embeddings(),
    )


def search_similar(collection_name: str, query: str, top_k: int = 5) -> list:
    """
    Find top_k most relevant chunks for a query.

    Returns:
        List of LangChain Document objects
    """
    vs = get_vectorstore(collection_name)
    results = vs.similarity_search(query, k=top_k)
    logger.info(
        "VECTORSTORE | Search '%s…' → %d results",
        query[:40], len(results)
    )
    return results