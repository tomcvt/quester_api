import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.dependencies import get_current_user

WEB_ROOT = os.path.join(os.path.dirname(__file__), "static")

UNGUARDED = {"index", "login", "register"}

router = APIRouter()


def _resolve_path(file_path: str) -> str | None:
    """
    Resolve a URL path to an absolute file path inside WEB_ROOT.
    Returns None if the file does not exist.
    Tries exact match first, then appends .html if no extension given.
    """
    # Normalise and prevent path traversal
    clean = os.path.normpath(file_path.lstrip("/"))
    if clean.startswith(".."):
        return None

    candidate = os.path.join(WEB_ROOT, clean)

    if os.path.isfile(candidate):
        return candidate

    # No extension supplied — try .html
    if not os.path.splitext(clean)[1]:
        html_candidate = candidate + ".html"
        if os.path.isfile(html_candidate):
            return html_candidate

    return None


def _is_allowed_extension(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in (".html", ".js")


def _stem(path: str) -> str:
    """Return the base filename without extension, lowercased."""
    return os.path.splitext(os.path.basename(path))[0].lower()


@router.get("/", include_in_schema=False)
async def serve_index():
    index_path = os.path.join(WEB_ROOT, "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path)


@router.get("/{file_path:path}", include_in_schema=False)
async def serve_static(
    file_path: str,
    user=Depends(get_current_user),
):
    resolved = _resolve_path(file_path)

    if resolved is None or not _is_allowed_extension(resolved):
        raise HTTPException(status_code=404)

    # Guard all pages except index and login
    if _stem(resolved) not in UNGUARDED and user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    return FileResponse(resolved)
