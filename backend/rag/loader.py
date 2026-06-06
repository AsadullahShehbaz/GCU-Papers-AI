import logging
import hashlib
import base64
import httpx
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
from config import settings

logger = logging.getLogger("gcul_api.rag.loader")

GEMINI_MODEL  = "gemini-2.5-flash"
CHUNK_SIZE    = 600
CHUNK_OVERLAP = 150


def pdf_url_to_collection_name(pdf_url: str) -> str:
    url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
    return f"paper_{url_hash}"


# ── Single underscore = accessible, double = private/broken ──
def _extract_with_gemini_b64(pdf_b64: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)               # ← use api_key param
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[{
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": pdf_b64,                 # ← use pdf_b64 param
                    }
                },
                {
                    "text": (
                        "Extract all text from this PDF. "
                        "Include all questions, tables, and any text visible "
                        "in images or scanned pages. "
                        "Preserve structure with line breaks between sections. "
                        "Do not summarize — extract everything verbatim."
                    )
                }
            ]
        }]
    )
    return response.text


async def load_and_chunk_pdf(pdf_url: str) -> list:
    logger.info("LOADER | Downloading PDF: %s", pdf_url)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(pdf_url, follow_redirects=True)

    if response.status_code != 200:
        raise Exception(f"Failed to download PDF: HTTP {response.status_code}")

    pdf_bytes = response.content
    logger.info("LOADER | Downloaded %.1f KB", len(pdf_bytes) / 1024)

    try:
        pdf_b64   = base64.b64encode(pdf_bytes).decode("utf-8")
        full_text = _extract_with_gemini_b64(pdf_b64, settings.GOOGLE_API_KEY)
    except Exception as e:
        logger.error("LOADER | Gemini extraction failed: %s", e)
        raise Exception(f"Gemini extraction failed: {e}")

    if not full_text or not full_text.strip():
        raise Exception("Gemini returned empty text — PDF may be corrupted")

    logger.info("LOADER | Extracted %d characters", len(full_text))

    doc = Document(
        page_content=full_text,
        metadata={
            "source": pdf_url,
            "extraction_method": "gemini",
        }
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_documents([doc])   # ← [doc] not valid_pages
    logger.info("LOADER | Split into %d chunks", len(chunks))

    return chunks
