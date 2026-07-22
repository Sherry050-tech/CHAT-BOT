"""
chat_router.py  -  The "doors" for everything chat related.

My job here is ONLY to:
  1. Receive the request
  2. Check the input is not garbage
  3. Call the right function from chat_service (Shehryar's file)
  4. Return whatever it gives back

There is no chat logic, no database code, and no AI code in this file.
"""

from fastapi import APIRouter, HTTPException

# Zainab's file - these describe the SHAPE of the data coming in and going out
from app.models import ChatRequest, ChatResponse, ThreadSummary, RenameThreadRequest

# Shehryar's file - this does the actual thinking
from app.services import chat_service


# A router is just a group of related endpoints.
# main.py picks this up with include_router() and attaches it to the app.
router = APIRouter(tags=["chat"])


# ============================================================
# POST /chat  ->  send a message, get the bot's reply
# ============================================================
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    POST means "I am sending you data to process".

    FastAPI already checked that `request` matches the ChatRequest model,
    so I know request.message exists and is a string.
    But FastAPI does NOT check if the string is empty, so I check that myself.
    """

    # Validation: reject empty or whitespace-only messages.
    # 400 means "bad request" - the user sent something wrong.
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    # Hand it over to the service. If thread_id is None,
    # the service creates a brand new conversation thread.
    result = chat_service.send_message(
        thread_id=request.thread_id,
        message=request.message,
    )

    # The service returns a plain dictionary like {"thread_id": ..., "reply": ...}
    # I wrap it in the ChatResponse model so the output shape is guaranteed.
    return ChatResponse(**result)


# ============================================================
# GET /threads  ->  list all past conversations
# ============================================================
@router.get("/threads", response_model=list[ThreadSummary])
def get_threads():
    """
    GET means "just give me data back, don't change anything".
    This one needs no input at all.
    """

    # Ask the service for the list of threads
    threads = chat_service.list_threads()

    # Each item is a dictionary, convert each one into a ThreadSummary model
    return [ThreadSummary(**thread) for thread in threads]


# ============================================================
# PATCH /threads/{thread_id}  ->  rename a conversation
# ============================================================
@router.patch("/threads/{thread_id}")
def rename_thread(thread_id: str, request: RenameThreadRequest):
    """
    PATCH means "update part of something that already exists".

    {thread_id} in the URL is a "path parameter".
    FastAPI automatically pulls it out of the URL and hands it to me
    as the `thread_id` argument. The new title comes in the request body.
    """

    # Validation: a thread cannot be renamed to nothing
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="title cannot be empty")

    # The service returns True if it found and renamed the thread, False if not
    found = chat_service.rename_thread(thread_id, request.title)

    # 404 means "not found" - the user asked for something that does not exist
    if not found:
        raise HTTPException(status_code=404, detail="thread not found")

    return {"status": "renamed", "thread_id": thread_id, "title": request.title}


# ============================================================
# DELETE /threads/{thread_id}  ->  delete a conversation
# ============================================================
@router.delete("/threads/{thread_id}")
def delete_thread(thread_id: str):
    """
    DELETE means exactly what it sounds like - remove this data.
    """

    # Same pattern: service returns True if it found and deleted it
    found = chat_service.delete_thread(thread_id)

    if not found:
        raise HTTPException(status_code=404, detail="thread not found")

    return {"status": "deleted", "thread_id": thread_id}
