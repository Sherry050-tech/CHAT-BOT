"""
upload_router.py  -  The "door" for uploading a file.

My job here is ONLY to receive the file and check it is safe to accept
(right file type, not too big, not empty), then hand it to rag_service.

The actual text extraction, chunking, and embedding is Rania's work.
None of that logic lives in this file.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException

# Zainab's file - describes the shape of the response I send back
from app.models import UploadResponse

# Rania's file - does the actual file processing
from app.services import rag_service


router = APIRouter(tags=["upload"])


# My own rules for what files I will accept.
# Keeping these at the top makes them easy to change later.
MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md"]


# ============================================================
# POST /upload  ->  upload a document so the bot can answer questions about it
# ============================================================
@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Note this function is `async def` instead of plain `def`.

    Reading a file takes time, and `async` lets the server handle other
    requests while it waits instead of freezing. That is also why we
    write `await file.read()` below instead of just `file.read()`.

    `File(...)` tells FastAPI this endpoint expects an actual uploaded file,
    not JSON. The `...` just means "this is required".
    """

    # Get the filename, or empty string if there somehow isn't one
    filename = file.filename or ""

    # CHECK 1: is the file type allowed?
    # Split "report.pdf" on the last dot to get "pdf", then add the dot back.
    if "." in filename:
        extension = "." + filename.rsplit(".", 1)[-1].lower()
    else:
        extension = ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"file type '{extension}' not allowed. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Now actually read the file contents into memory as raw bytes
    file_bytes = await file.read()

    # CHECK 2: is the file empty?
    if not file_bytes:
        raise HTTPException(status_code=400, detail="uploaded file is empty")

    # CHECK 3: is the file too big?
    # len(file_bytes) gives bytes, so divide twice by 1024 to get megabytes.
    size_in_mb = len(file_bytes) / 1024 / 1024
    if size_in_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"file is {size_in_mb:.1f}MB, maximum allowed is {MAX_FILE_SIZE_MB}MB",
        )

    # All checks passed, hand the file over to Rania's service.
    # It returns something like {"file_id": "...", "chunks_stored": 12}
    result = rag_service.process_uploaded_file(filename, file_bytes)

    # Send the result back in the shape defined by the UploadResponse model
    return UploadResponse(
        file_id=result["file_id"],
        filename=filename,
        chunks_stored=result["chunks_stored"],
    )