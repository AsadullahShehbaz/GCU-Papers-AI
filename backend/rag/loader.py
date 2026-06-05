import logging
import hashlib
import tempfile
import os  # <-- Added to cleanly manage temp files
import httpx
from langchain_community.document_loaders.parsers.pdf import RapidOCRBlobParser
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("gcul_api.rag.loader")

CHUNK_SIZE    = 600
CHUNK_OVERLAP = 150


def pdf_url_to_collection_name(pdf_url: str) -> str:
    url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
    return f"paper_{url_hash}"


async def load_and_chunk_pdf(pdf_url: str) -> list:
    logger.info("LOADER | Downloading PDF: %s", pdf_url)

    # 1. Download PDF bytes
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(pdf_url, follow_redirects=True)

    if response.status_code != 200:
        raise Exception(f"Failed to download PDF: HTTP {response.status_code}")

    pdf_bytes = response.content
    logger.info("LOADER | Downloaded %.1f KB", len(pdf_bytes) / 1024)

    # 2. Save to temp file & close it safely so other processes can read it
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name  # Grab the path
        
        # File is now closed and safe to read on Windows!

        # 3. Load pages with PyPDFLoader + RapidOCR
        loader = PyPDFLoader(
            tmp_path, 
            extract_images=True, 
            images_parser=RapidOCRBlobParser()
        )
        
        pages = loader.load()
        logger.info("LOADER | Loaded %d raw pages", len(pages))
        
        # Filter and log the actual text captured
        valid_pages = []
        for i, page in enumerate(pages):
            content_sample = page.page_content.strip()
            if content_sample:
                valid_pages.append(page)
                # Useful debug trace to verify OCR content extraction in terminal
                logger.info("LOADER | Page %d has text content sample: %s...", i+1, repr(content_sample[:50]))
            else:
                logger.warning("LOADER | Page %d extracted text was empty!", i+1)

        if not valid_pages:
            logger.error("LOADER | Failed to pull text content even after attempting OCR!")
            return []

        # 4. Split into chunks using validated data
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len
        )

        chunks = splitter.split_documents(valid_pages)  # <-- Fixed: passing valid_pages
        logger.info("LOADER | Split into %d chunks", len(chunks))

        return chunks

    finally:
        # Clean up filesystem by removing the temp file when finished
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                logger.warning("LOADER | Cleanup failed for temporary file: %s", e)