from database import threads_collection, messages_collection, users_collection, chunks_collection
from models import ChatMessage, Thread, User, DocumentChunk

# ---------- MESSAGES ----------

def create_message(message: ChatMessage) -> ChatMessage:
    messages_collection.insert_one(message.model_dump())
    return message

def get_thread_history(thread_id: str) -> list[dict]:
    cursor = messages_collection.find({"thread_id": thread_id}).sort("timestamp", 1)
    return list(cursor)

# ---------- THREADS ----------

def create_thread(thread: Thread) -> Thread:
    threads_collection.insert_one(thread.model_dump())
    return thread

def get_threads_for_user(user_id: str) -> list[dict]:
    cursor = threads_collection.find({"user_id": user_id}).sort("created_at", -1)
    return list(cursor)

def update_thread_title(thread_id: str, new_title: str) -> bool:
    result = threads_collection.update_one(
        {"id": thread_id}, {"$set": {"title": new_title}}
    )
    return result.modified_count > 0

def delete_thread(thread_id: str) -> bool:
    threads_collection.delete_one({"id": thread_id})
    messages_collection.delete_many({"thread_id": thread_id})
    return True

# ---------- USERS ----------

def create_user(user: User) -> User:
    users_collection.insert_one(user.model_dump())
    return user

def get_user_by_id(user_id: str) -> dict | None:
    return users_collection.find_one({"id": user_id})

# ---------- DOCUMENT CHUNKS (for RAG) ----------

def create_document_chunk(chunk: DocumentChunk) -> DocumentChunk:
    chunks_collection.insert_one(chunk.model_dump())
    return chunk

def get_chunks_for_thread(thread_id: str) -> list[dict]:
    cursor = chunks_collection.find({"thread_id": thread_id})
    return list(cursor)