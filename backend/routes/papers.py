# ============================================================
# routes/papers.py — Paper endpoints
#
# GET  /papers         → return all approved papers
# POST /papers/upload  → upload PDF + save metadata
# ============================================================

import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Paper
from github import upload_pdf_to_github

router = APIRouter(prefix="/papers", tags=["papers"])


# ── Helpers ───────────────────────────────────────────────────

def sanitize_filename(subject: str, semester: int, year: int) -> str:
    """
    Build a clean, safe filename from paper metadata.
    e.g. "Data Structures & Algorithms" → "data_structures_algorithms_sem3_2024.pdf"
    """
    clean = subject.lower()
    clean = re.sub(r"[^a-z0-9\s]", "", clean)   # remove special chars
    clean = re.sub(r"\s+", "_", clean.strip())   # spaces → underscores
    return f"{clean}_sem{semester}_{year}.pdf"


def validate_pdf(file: UploadFile):
    """Raise error if file is not a PDF or too large (10MB max)."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    # size check happens after reading — see upload route


# ── GET /papers ───────────────────────────────────────────────

@router.get("/")
async def get_papers(db: AsyncSession = Depends(get_db)):
    """Return all approved papers. Frontend fetches this instead of data.json."""
    result = await db.execute(
        select(Paper)
        .where(Paper.status == "approved")
        .order_by(Paper.created_at.desc())
    )
    papers = result.scalars().all()
    return [p.to_dict() for p in papers]


# ── POST /papers/upload ───────────────────────────────────────

@router.post("/upload")
async def upload_paper(
    # Form fields
    subject:     str = Form(...),
    semester:    int = Form(...),
    year:        int = Form(...),
    type:        str = Form(...),
    department:  str = Form(...),
    uploaded_by: str = Form(...),   # user email from Google login

    # File
    file: UploadFile = File(...),

    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF to GitHub and save paper metadata to Neon DB.
    Auto-approved — appears on site immediately.
    """
    # 1. Validate file type
    validate_pdf(file)

    # 2. Read file bytes
    file_bytes = await file.read()

    # 3. Reject if file too large (10MB)
    MAX_SIZE = 10 * 1024 * 1024   # 10 MB
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    # 4. Build clean filename
    filename = sanitize_filename(subject, semester, year)

    # 5. Upload to GitHub → get public URL
    try:
        pdf_url = await upload_pdf_to_github(filename, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 6. Save metadata to Neon DB (auto-approved)
    paper = Paper(
        subject=     subject,
        semester=    semester,
        year=        year,
        type=        type,
        department=  department,
        pdf_url=     pdf_url,
        uploaded_by= uploaded_by,
        status=      "approved",
    )
    db.add(paper)
    # commit happens automatically in get_db dependency

    return {
        "message": "Paper uploaded successfully!",
        "pdf_url": pdf_url,
        "subject": subject,
    }