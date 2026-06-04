# ============================================================
# github.py — GitHub file upload service
# Uploads PDF bytes to your GitHub repo via GitHub API
# Returns the public raw URL of the uploaded file
# ============================================================

import base64
import httpx
from config import settings


# GitHub API base
GITHUB_API = "https://api.github.com"

# Auth headers — reused for every request
HEADERS = {
    "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
    "Accept":        "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def build_file_path(filename: str) -> str:
    """Build path inside repo: pdf/filename.pdf"""
    return f"{settings.GITHUB_PDF_FOLDER}/{filename}"


def build_raw_url(filename: str) -> str:
    """Build public raw URL to access the PDF."""
    return (
        f"https://raw.githubusercontent.com/"
        f"{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/"
        f"{settings.GITHUB_BRANCH}/{settings.GITHUB_PDF_FOLDER}/{filename}"
    )


async def upload_pdf_to_github(filename: str, file_bytes: bytes) -> str:
    """
    Upload a PDF file to GitHub repo.

    Args:
        filename:   clean filename e.g. "dsa_sem3_2024.pdf"
        file_bytes: raw bytes of the PDF

    Returns:
        Public raw URL of the uploaded file

    Raises:
        Exception if upload fails
    """
    file_path = build_file_path(filename)
    api_url   = f"{GITHUB_API}/repos/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/contents/{file_path}"

    # GitHub requires base64 encoded content
    encoded_content = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "message": f"Add paper: {filename}",   # commit message
        "content": encoded_content,
        "branch":  settings.GITHUB_BRANCH,
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(api_url, json=payload, headers=HEADERS)

    if response.status_code not in (200, 201):
        raise Exception(f"GitHub upload failed: {response.status_code} — {response.text}")

    return build_raw_url(filename)