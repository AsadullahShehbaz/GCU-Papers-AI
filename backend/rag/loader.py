import logging
import hashlib
import tempfile
import os  # <-- Added to cleanly manage temp files
import httpx
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
from config import settings
logger = logging.getLogger("gcul_api.rag.loader")
GEMINI_MODEL = "gemini-2.5-flash"
CHUNK_SIZE    = 600
CHUNK_OVERLAP = 150


def pdf_url_to_collection_name(pdf_url: str) -> str:
    url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
    return f"paper_{url_hash}"


def extract_text_with_gemini(pdf_bytes: bytes)->str:
    logger.info('Loader | Sending pdfs to gemini for extraction text')
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            {
                "parts":[
                    {
                        "inline_data" : {
                            "mime_type": "application/pdf",
                            "data" : pdf_bytes
                        }
                    },
                    {
                        "text" : "Extract all text from this PDF .Include all questions , table , any text visible in images or scanned pages.Preserve structure with line breaks between sections.Don't summarize , extract everything verbatim.",

                    }
                ]

            },
        ]
    )
    extracted =  response.text
    logger.info(f'Loader | Gemini extracted {len(extracted)} characters')
    return extracted

async def load_and_chunk_pdf(pdf_url: str) -> list:
    logger.info("LOADER | Downloading PDF: %s", pdf_url)

    # 1. Download PDF bytes
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(pdf_url, follow_redirects=True)

    if response.status_code != 200:
        raise Exception(f"Failed to download PDF: HTTP {response.status_code}")

    pdf_bytes = response.content
    logger.info("LOADER | Downloaded %.1f KB", len(pdf_bytes) / 1024)

    # 2. 
    try:
        import base64
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        full_text = _extract_with_geminib64(pdf_b64,settings.GOOGLE_API_KEY)
    except Exception as e:
        logger.info(f'Loader | Gemini Extraction Failed : {e}')
        raise Exception(f'Gemini Extraction Failed : {e}')
   
  

    if not full_text or not full_text.strip():
        raise Exception('Gemini returned empty text - pdf may be currupted ')
    
    logger.info(f'Loader | Gemini Extracted {len(full_text)} characters')

    doc = Document(
    page_content = full_text,
    metadata = {
        "source": pdf_url,
        "extraction_method": "gemini",
    }
)
    # 4. Split into chunks using validated data
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n",". ",", "," ",""],
        length_function=len
    )

    chunks = splitter.split_documents(valid_pages)  # <-- Fixed: passing valid_pages
    logger.info("LOADER | Split into %d chunks", len(chunks))

    return chunks

def __extract_with_geminib64(pdf_b64 : str ,api_key : str)-> str :
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            {
                "parts":[
                    {
                        "inline_data" : {
                            "mime_type": "application/pdf",
                            "data" : pdf_bytes
                        }
                    },
                    {
                        "text" : "Extract all text from this PDF .Include all questions , table , any text visible in images or scanned pages.Preserve structure with line breaks between sections.Don't summarize , extract everything verbatim.",

                    }
                ]

            },
        ]
    )
    extracted =  response.text
    return extracted