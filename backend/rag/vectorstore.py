import logging
from typing import List

from langchain.embeddings.base import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from google import genai

from config import settings

logger = logging.getLogger("gcul_api.rag.vectorstore")

EMBEDDING_MODEL = "gemini-embedding-001"

# ============================================================
# Global cached clients
# ============================================================

_embeddings_client = None
_qdrant_client = None


# ============================================================
# Embeddings
# ============================================================

def get_embeddings_client():
    global _embeddings_client

    if _embeddings_client is None:
        _embeddings_client = genai.Client(
            api_key=settings.GOOGLE_API_KEY
        )
        logger.info("EMBEDDINGS | Google GenAI client initialized")

    return _embeddings_client


def embed_documents(texts: List[str]) -> List[List[float]]:
    client = get_embeddings_client()

    logger.info(
        "EMBEDDINGS | Embedding %d documents...",
        len(texts)
    )

    embeddings = []

    for i, text in enumerate(texts):

        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )

        embeddings.append(
            result.embeddings[0].values
        )

        if (i + 1) % 20 == 0:
            logger.info(
                "EMBEDDINGS | Progress: %d/%d",
                i + 1,
                len(texts)
            )

    logger.info("EMBEDDINGS | Done")

    return embeddings


def embed_query(text: str) -> List[float]:
    client = get_embeddings_client()

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    logger.info(f"EMBEDDINGS Size {len(result.embeddings[0].values)}")

    return result.embeddings[0].values
def get_vector_size():
    return len(embed_query("test"))
VECTOR_SIZE = get_vector_size()


# ============================================================
# LangChain Wrapper
# ============================================================

class EmbeddingWrapper(Embeddings):

    def embed_documents(self, texts):
        return embed_documents(texts)

    def embed_query(self, text):
        VECTOR_SIZE = len(embed_query(text))
        logger.info("VECTOR SIZE =", VECTOR_SIZE)
        return embed_query(text)


# Single reusable wrapper
embedding_wrapper = EmbeddingWrapper()


# ============================================================
# Qdrant
# ============================================================

def get_qdrant_client():
    global _qdrant_client

    if _qdrant_client is None:

        _qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )

        logger.info(
            "VECTORSTORE | Qdrant client connected"
        )

    return _qdrant_client


# ============================================================
# Collections
# ============================================================

def collection_exists(collection_name: str) -> bool:

    
    client = get_qdrant_client()

    existing = [
        c.name
        for c in client.get_collections().collections
    ]

    exists = collection_name in existing

    logger.info(
        "VECTORSTORE | Collection '%s' exists: %s",
        collection_name,
        exists,
    )

    return exists


def create_collection(collection_name: str):

    client = get_qdrant_client()

    logger.info(
        "VECTORSTORE | Creating collection: %s",
        collection_name
    )

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )


# ============================================================
# Indexing
# ============================================================

def index_chunks(
    collection_name: str,
    chunks: list,
) -> QdrantVectorStore:

    logger.info(
        "VECTORSTORE | Indexing %d chunks -> '%s'",
        len(chunks),
        collection_name,
    )

    vectorstore = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embedding_wrapper,
        collection_name=collection_name,
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        timeout=180.0,
    )

    logger.info(
        "VECTORSTORE | Indexed collection=%s",
        collection_name,
    )

    return vectorstore


def create_and_index(
    collection_name: str,
    chunks: list,
) -> QdrantVectorStore:

    create_collection(collection_name)

    return index_chunks(
        collection_name,
        chunks,
    )


# ============================================================
# Search
# ============================================================

def get_vectorstore(
    collection_name: str,
) -> QdrantVectorStore:

    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=collection_name,
        embedding=embedding_wrapper,
    )


def search_similar(
    collection_name: str,
    query: str,
    top_k: int = 5,
):

    vs = get_vectorstore(collection_name)

    results = vs.similarity_search(
        query,
        k=top_k,
    )

    logger.info(
        "VECTORSTORE | Search '%s...' -> %d results",
        query[:40],
        len(results),
    )

    return results