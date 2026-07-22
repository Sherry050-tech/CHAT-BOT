"""
upload_router.py  -  The "door" for uploading a file.

My job here is ONLY to receive the file, check it is safe to accept
(right type, not too big, not empty), then hand it to rag_service.

The actual text extraction, chunking, and embedding is Rania's work.
None of that logic lives in this file.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.models import UploadResponse
from app.services import rag_service

# Used only to create a thread when the user uploads before chatting
from app.services import chat_service


router = APIRouter(tags=["upload"])


# Same placeholder user as the chat router, until login exists
DEFAULT_USER_ID = "anon"


# My own rules for what files I will accept
MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md"]


# ============================================================
# POST /upload  ->  upload a document so the bot can answer questions about it
# ============================================================
@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    thread_id: str | None = Form(None),
):
    """
    Every stored chunk has to be linked to a conversation, because
    DocumentChunk requires a thread_id and the bot needs to know which
    chat a document belongs to.

    thread_id is optional here on purpose: the user can upload a file
    before sending any message, in which case there is no thread yet.
    When that happens we create one, and send its id back so the
    frontend can keep using it for the rest of the conversation.

    This is `async def` because reading a file takes time, and async lets
    the server serve other requests while it waits.
    """

    if not thread_id or not thread_id.strip():
        thread_id = chat_service.get_or_create_thread(None, DEFAULT_USER_ID)

    filename = file.filename or ""

    # CHECK 1: is the file type allowed?
    if "." in filename:
        extension = "." + filename.rsplit(".", 1)[-1].lower()
    else:
        extension = ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"file type '{extension}' not allowed. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Read the file contents into memory as raw bytes
    file_bytes = await file.read()

    # CHECK 2: is the file empty?
    if not file_bytes:
        raise HTTPException(status_code=400, detail="uploaded file is empty")

    # CHECK 3: is the file too big?
    size_in_mb = len(file_bytes) / 1024 / 1024
    if size_in_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"file is {size_in_mb:.1f}MB, maximum allowed is {MAX_FILE_SIZE_MB}MB",
        )

    # All checks passed, hand it over to Rania's service.
    # It returns {"file_id": ..., "chunks_stored": ...}
    result = rag_service.process_uploaded_file(thread_id, filename, file_bytes)

    return UploadResponse(
        file_id=result["file_id"],
        filename=filename,
        thread_id=thread_id,
        chunks_stored=result["chunks_stored"],
    )