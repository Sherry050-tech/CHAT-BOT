from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


class ChatMessage(BaseModel):
    id: str = Field(default_factory=new_id)
    thread_id: str
    sender: Literal["user", "bot"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Thread(BaseModel):
    id: str = Field(default_factory=new_id)
    user_id: str
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    id: str = Field(default_factory=new_id)
    username: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    id: str = Field(default_factory=new_id)
    thread_id: str
    source_filename: str
    chunk_text: str
    embedding: list[float]
    chunk_index: int

class ChatRequest(BaseModel):
    thread_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    thread_id: str
    reply: str

class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    updated_at: datetime

class RenameThreadRequest(BaseModel):
    title: str

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    thread_id: str
    chunks_stored: int