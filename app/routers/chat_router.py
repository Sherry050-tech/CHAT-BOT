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

# Zainab's file - the shapes of data going in and out of the API
from app.models import ChatRequest, ChatResponse, ThreadSummary, RenameThreadRequest

# Shehryar's file - this does the actual thinking
from app.services import chat_service


router = APIRouter(tags=["chat"])


# Temporary user id. We have no login system yet, so every request is
# treated as coming from the same user. Replace this once auth exists.
DEFAULT_USER_ID = "anon"


# ============================================================
# POST /chat  ->  send a message, get the bot's reply
# ============================================================
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    FastAPI already checked that request matches ChatRequest,
    so message exists and is a string. It does NOT check for an
    empty string though, so I check that myself.
    """

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    # Shehryar's function is generate_reply, and it expects the argument
    # named user_message (not message). It creates a new thread by itself
    # when thread_id is None.
    result = chat_service.generate_reply(
        thread_id=request.thread_id,
        user_message=request.message,
        user_id=DEFAULT_USER_ID,
    )

    return ChatResponse(**result)


# ============================================================
# GET /threads  ->  list all past conversations
# ============================================================
@router.get("/threads", response_model=list[ThreadSummary])
def get_threads():
    """
    Returns the list of conversations for the current user.
    """

    threads = chat_service.list_threads(user_id=DEFAULT_USER_ID)

    # The database stores the thread's id in a field called "id",
    # but the API sends it out as "thread_id", so I rename it here.
    # A brand new thread may not have updated_at yet, so I fall back
    # to created_at in that case.
    return [
        ThreadSummary(
            thread_id=thread["id"],
            title=thread["title"],
            updated_at=thread.get("updated_at") or thread["created_at"],
        )
        for thread in threads
    ]


# ============================================================
# PATCH /threads/{thread_id}  ->  rename a conversation
# ============================================================
@router.patch("/threads/{thread_id}")
def rename_thread(thread_id: str, request: RenameThreadRequest):
    """
    {thread_id} is a path parameter - FastAPI pulls it out of the URL
    automatically. The new title comes in the request body.
    """

    if not request.title.strip():
        raise HTTPException(status_code=400, detail="title cannot be empty")

    # Returns True if the thread was found and renamed, False if not
    found = chat_service.rename_thread(thread_id, request.title)

    if not found:
        raise HTTPException(status_code=404, detail="thread not found")

    return {"status": "renamed", "thread_id": thread_id, "title": request.title}


# ============================================================
# DELETE /threads/{thread_id}  ->  delete a conversation
# ============================================================
@router.delete("/threads/{thread_id}")
def delete_thread(thread_id: str):
    found = chat_service.delete_thread(thread_id)

    if not found:
        raise HTTPException(status_code=404, detail="thread not found")

    return {"status": "deleted", "thread_id": thread_id}