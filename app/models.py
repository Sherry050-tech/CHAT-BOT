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