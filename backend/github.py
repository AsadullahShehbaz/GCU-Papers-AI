# ============================================================
# github.py — GitHub file upload service
# ============================================================

import base64
import logging

import httpx

from config import settings

logger = logging.getLogger("gcul_api.github")   # child of root logger in main.py

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
    "Accept":        "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def build_file_path(filename: str) -> str:
    path = f"{settings.GITHUB_PDF_FOLDER}/{filename}"
    logger.debug("GITHUB | build_file_path → '%s'", path)
    return path


def build_raw_url(filename: str) -> str:
    url = (
        f"https://raw.githubusercontent.com/"
        f"{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/"
        f"{settings.GITHUB_BRANCH}/{settings.GITHUB_PDF_FOLDER}/{filename}"
    )
    logger.debug("GITHUB | build_raw_url → %s", url)
    return url


async def upload_pdf_to_github(filename: str, file_bytes: bytes) -> str:
    """
    Upload a PDF file to GitHub repo.
    Returns the public raw URL of the uploaded file.
    """
    size_kb    = len(file_bytes) / 1024
    file_path  = build_file_path(filename)
    api_url    = (
        f"{GITHUB_API}/repos/{settings.GITHUB_REPO_OWNER}/"
        f"{settings.GITHUB_REPO_NAME}/contents/{file_path}"
    )

    logger.info(
        "GITHUB | START  filename='%s'  size=%.1f KB  repo=%s/%s  branch=%s",
        filename, size_kb,
        settings.GITHUB_REPO_OWNER, settings.GITHUB_REPO_NAME,
        settings.GITHUB_BRANCH,
    )
    logger.debug("GITHUB | PUT %s", api_url)

    # Encode — log timing so you can spot slow base64 on large files
    encoded_content = base64.b64encode(file_bytes).decode("utf-8")
    logger.debug("GITHUB | base64 encoded → %d chars", len(encoded_content))

    payload = {
        "message": f"Add paper: {filename}",
        "content": encoded_content,
        "branch":  settings.GITHUB_BRANCH,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("GITHUB | Sending PUT request to GitHub API...")
            response = await client.put(api_url, json=payload, headers=HEADERS)
    except httpx.TimeoutException:
        logger.error(
            "GITHUB | Request timed out after 30s  (filename='%s')", filename
        )
        raise Exception(f"GitHub upload timed out for '{filename}'.")
    except httpx.RequestError as exc:
        logger.error(
            "GITHUB | Network error during upload  (filename='%s')  error=%s",
            filename, exc,
        )
        raise Exception(f"GitHub network error: {exc}")

    logger.debug(
        "GITHUB | Response  status=%d  headers=%s",
        response.status_code,
        dict(response.headers),
    )

    # 422 means the file already exists in the repo
    if response.status_code == 422:
        logger.warning(
            "GITHUB | File already exists in repo  (filename='%s') — skipping upload",
            filename,
        )
        raw_url = build_raw_url(filename)
        logger.info("GITHUB | Returning existing URL → %s", raw_url)
        return raw_url

    if response.status_code not in (200, 201):
        logger.error(
            "GITHUB | Upload failed  status=%d  filename='%s'  response=%s",
            response.status_code, filename, response.text[:300],   # cap at 300 chars
        )
        raise Exception(
            f"GitHub upload failed: {response.status_code} — {response.text}"
        )

    raw_url = build_raw_url(filename)
    logger.info(
        "GITHUB | DONE ✓  filename='%s'  status=%d  url=%s",
        filename, response.status_code, raw_url,
    )
    return raw_url
