# ============================================================
# rag/loader.py — PDF Loading & Chunking
# Downloads PDF from URL, splits into overlapping chunks
# ============================================================

import logging
import hashlib
import tempfile
import httpx

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger("gcul_api.rag.loader")

# ── Chunk settings ────────────────────────────────────────────
# chunk_size: characters per chunk (not tokens)
# chunk_overlap: overlap between chunks so context isn't lost at boundaries
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150


def pdf_url_to_collection_name(pdf_url: str) -> str:
    """
    Convert a PDF URL to a safe, unique Qdrant collection name.
    e.g. "https://raw.github.../dsa.pdf" → "paper_a3f9c1b2"

    Qdrant collection names must be alphanumeric + underscores only.
    """
    url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
    return f"paper_{url_hash}"


async def load_and_chunk_pdf(pdf_url: str) -> list:
    """
    Download PDF from URL, load pages, split into chunks.

    Returns:
        List of LangChain Document objects with page_content + metadata

    Raises:
        Exception if download or parsing fails
    """
    logger.info("LOADER | Downloading PDF: %s", pdf_url)

    # 1. Download PDF bytes
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(pdf_url, follow_redirects=True)

    if response.status_code != 200:
        raise Exception(f"Failed to download PDF: HTTP {response.status_code}")

    pdf_bytes = response.content
    logger.info("LOADER | Downloaded %.1f KB", len(pdf_bytes) / 1024)

    # 2. Save to temp file — PyPDFLoader needs a file path
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    # 3. Load pages with PyPDFLoader
    loader = PyPDFLoader(tmp_path)
    pages  = loader.load()
    logger.info("LOADER | Loaded %d pages", len(pages))

    if not pages:
        raise Exception("PDF appears to be empty or unreadable")

    # 4. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(pages)
    logger.info("LOADER | Split into %d chunks", len(chunks))

    return chunks