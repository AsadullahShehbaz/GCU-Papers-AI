# ============================================================
# routes/papers.py — Paper endpoints
#
# GET  /papers         → return all approved papers
# POST /papers/upload  → upload PDF + save metadata
# ============================================================

import logging
import re

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Paper
from github import upload_pdf_to_github

router = APIRouter(prefix="/papers", tags=["papers"])
logger = logging.getLogger("gcul_api.papers")   # child of the root logger in main.py


# ── Helpers ───────────────────────────────────────────────────

def sanitize_filename(subject: str, semester: int, year: int) -> str:
    """
    Build a clean, safe filename from paper metadata.
    e.g. "Data Structures & Algorithms" → "data_structures_algorithms_sem3_2024.pdf"
    """
    clean = subject.lower()
    clean = re.sub(r"[^a-z0-9\s]", "", clean)
    clean = re.sub(r"\s+", "_", clean.strip())
    filename = f"{clean}_sem{semester}_{year}.pdf"
    logger.debug("FILENAME | '%s' → '%s'", subject, filename)
    return filename


def validate_pdf(file: UploadFile):
    """Raise error if file is not a PDF."""
    logger.debug("VALIDATE | content_type=%s  filename=%s", file.content_type, file.filename)
    if file.content_type != "application/pdf":
        logger.warning(
            "VALIDATE | Rejected non-PDF upload: content_type=%s  filename=%s",
            file.content_type, file.filename,
        )
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")


# ── GET /papers ───────────────────────────────────────────────

@router.get("/")
async def get_papers(db: AsyncSession = Depends(get_db)):
    """Return all approved papers."""
    logger.info("GET /papers | Fetching approved papers from DB")

    try:
        result = await db.execute(
            select(Paper)
            .where(Paper.status == "approved")
            .order_by(Paper.created_at.desc())
        )
        papers = result.scalars().all()
    except Exception:
        logger.exception("GET /papers | DB query failed")
        raise HTTPException(status_code=500, detail="Database error while fetching papers.")

    logger.info("GET /papers | Returning %d paper(s)", len(papers))
    return [p.to_dict() for p in papers]


# ── POST /papers/upload ───────────────────────────────────────

@router.post("/upload")
async def upload_paper(
    subject:     str = Form(...),
    semester:    int = Form(...),
    year:        int = Form(...),
    type:        str = Form(...),
    department:  str = Form(...),
    uploaded_by: str = Form(...),
    file:        UploadFile = File(...),
    db:          AsyncSession = Depends(get_db),
):
    """Upload a PDF to GitHub and save paper metadata to Neon DB."""

    logger.info(
        "UPLOAD | START  subject='%s'  sem=%d  year=%d  type=%s  dept=%s  by=%s  file=%s",
        subject, semester, year, type, department, uploaded_by, file.filename,
    )

    # 1. Validate file type
    validate_pdf(file)
    logger.info("UPLOAD | STEP 1 ✓  File type is PDF")

    # 2. Read file bytes
    file_bytes = await file.read()
    size_kb = len(file_bytes) / 1024
    logger.info("UPLOAD | STEP 2 ✓  Read %.1f KB from upload stream", size_kb)

    # 3. Size check (10 MB max)
    MAX_SIZE = 10 * 1024 * 1024
    if len(file_bytes) > MAX_SIZE:
        logger.warning(
            "UPLOAD | STEP 3 ✗  File too large: %.2f MB > 10 MB  (by=%s  subject='%s')",
            len(file_bytes) / (1024 * 1024), uploaded_by, subject,
        )
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    logger.info("UPLOAD | STEP 3 ✓  Size OK (%.1f KB)", size_kb)

    # 4. Build filename
    filename = sanitize_filename(subject, semester, year)
    logger.info("UPLOAD | STEP 4 ✓  Filename → '%s'", filename)

    # 5. Push to GitHub
    logger.info("UPLOAD | STEP 5    Pushing '%s' to GitHub...", filename)
    try:
        pdf_url = await upload_pdf_to_github(filename, file_bytes)
        logger.info("UPLOAD | STEP 5 ✓  GitHub URL → %s", pdf_url)
    except Exception:
        logger.exception(
            "UPLOAD | STEP 5 ✗  GitHub upload failed  (filename='%s'  by=%s)",
            filename, uploaded_by,
        )
        raise HTTPException(status_code=500, detail="Failed to upload PDF to GitHub.")

    # 6. Persist metadata to Neon DB
    logger.info("UPLOAD | STEP 6    Saving metadata to DB...")
    try:
        paper = Paper(
            subject=subject,
            semester=semester,
            year=year,
            type=type,
            department=department,
            pdf_url=pdf_url,
            uploaded_by=uploaded_by,
            status="approved",
        )
        db.add(paper)
        logger.info("UPLOAD | STEP 6 ✓  Metadata saved  (url=%s)", pdf_url)
    except Exception:
        logger.exception(
            "UPLOAD | STEP 6 ✗  DB insert failed  (subject='%s'  by=%s)",
            subject, uploaded_by,
        )
        raise HTTPException(status_code=500, detail="Failed to save paper metadata.")

    logger.info(
        "UPLOAD | DONE ✓  subject='%s'  sem=%d  year=%d  url=%s",
        subject, semester, year, pdf_url,
    )
    return {
        "message": "Paper uploaded successfully!",
        "pdf_url": pdf_url,
        "subject": subject,
    }