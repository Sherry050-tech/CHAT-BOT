"""
chat_service.py
----------------
Sheharyar's file.

Takes a user's message plus past history, sends it through LangChain,
gets a reply back, and saves the exchange to the database.

Updated to match team conventions:
- Sync (pymongo), not async (motor) — matches Zainab's database.py
- Uses `sender`/`timestamp` fields, not `role`/`created_at` — matches Zainab's ChatMessage model
- Uses Zainab's own `id` field (uuid string) for threads, not Mongo's `_id`
- Uses Rania's actual `retrieve_top_chunks` function/signature
- Adds list_threads / rename_thread / delete_thread for Mustafa's router
- Imports from app.database / app.models (shared app/ package)

New Additions:
- Tool Calling: Added `get_current_time` and the LangChain tool execution loop.
- Guardrails: Added input validation, try/except error fallbacks, and regex output cleaning.
"""

import os
import re
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from app.database import threads_collection
from app.models import ChatMessage, Thread
from app.crud import (
    create_message,
    get_thread_history,
    create_thread,
    get_threads_for_user,
    update_thread_title,
    delete_thread as crud_delete_thread,
    get_chunks_for_thread,
)
from app.services.rag_service import retrieve_top_chunks

# Upgraded to a model trained specifically for JSON tool calling
llm = ChatOpenAI(
    model='meta-llama/llama-3.1-8b-instruct:free',
    temperature=0.3,
    openai_api_key=os.getenv('OPENROUTER_API_KEY'),
    openai_api_base='https://openrouter.ai/api/v1',
)

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use the provided context from uploaded "
    "documents if it is relevant to the user's question. If no context "
    "is relevant, just answer normally. You have access to tools; use them if needed."
)

# ---------- 1. DEFINE TOOLS ----------

@tool
def get_current_time() -> str:
    """Always use this tool when the user asks for the current time, date, or day."""
    return f"The current server time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

# Group all available tools here
tools = [get_current_time]


# ---------- DATABASE/CRUD WRAPPERS ----------

def get_or_create_thread(thread_id: str | None, user_id: str) -> str:
    """Return an existing thread_id, or create a new thread and return its id."""
    if thread_id:
        return thread_id

    thread = Thread(user_id=user_id, title="New Conversation")
    create_thread(thread)
    return thread.id

def get_chat_history(thread_id: str, limit: int = 20) -> list[dict]:
    """Fetch the last `limit` messages in a thread, oldest first."""
    history = get_thread_history(thread_id)
    return history[-limit:]

def save_message(thread_id: str, sender: str, content: str):
    message = ChatMessage(thread_id=thread_id, sender=sender, content=content)
    create_message(message)

def touch_thread(thread_id: str):
    """Bump updated_at so this thread shows as most recently active."""
    threads_collection.update_one(
        {"id": thread_id}, {"$set": {"updated_at": datetime.utcnow()}}
    )

def get_context_for_thread(thread_id: str, question: str) -> str:
    """
    Pull stored chunks for this thread and run Rania's retrieval
    to get the most relevant ones for the current question.
    """
    stored_chunks = get_chunks_for_thread(thread_id)
    if not stored_chunks:
        return ""

    chunk_texts = [c["chunk_text"] for c in stored_chunks]
    chunk_vectors = [c["embedding"] for c in stored_chunks]

    top_chunks = retrieve_top_chunks(question, chunk_texts, chunk_vectors, top_k=3)
    return "\n\n".join(top_chunks)


# ---------- MAIN CHAT PIPELINE ----------

def generate_reply(thread_id: str | None, user_message: str, user_id: str = "anon") -> dict:
    """
    Main entry point: takes a message + thread, pulls history + RAG context,
    calls the LLM, handles any tool requests, saves both messages, and returns the reply.
    """
    thread_id = get_or_create_thread(thread_id, user_id)

    # GUARDRAIL 1: Input Validation
    # Stops empty messages or accidental spacebar hits from wasting API calls
    if not user_message or len(user_message.strip()) == 0:
        return {"thread_id": thread_id, "reply": "I didn't receive a message. How can I help?"}

    # 1. Pull relevant chunks from uploaded docs (RAG)
    context_text = get_context_for_thread(thread_id, user_message)

    # 2. Pull past conversation history
    history = get_chat_history(thread_id)

    # 3. Build the LangChain message list
    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    if context_text:
        lc_messages.append(SystemMessage(content=f"Relevant context:\n{context_text}"))

    for msg in history:
        if msg["sender"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        else:
            lc_messages.append(AIMessage(content=msg["content"]))

    lc_messages.append(HumanMessage(content=user_message))

    # Bind the tools to the LLM
    llm_with_tools = llm.bind_tools(tools)

    try:
        # 4. Call the LLM to see if it wants to use a tool or just answer
        response = llm_with_tools.invoke(lc_messages)
        
        # Check if the model generated a JSON tool request
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Add the AI's tool request to the message history
            lc_messages.append(response) 
            
            # Execute the requested tools
            for tool_call in response.tool_calls:
                if tool_call["name"] == "get_current_time":
                    tool_output = get_current_time.invoke(tool_call["args"])
                    
                    # Append the Python function's result back into the chat history
                    lc_messages.append(ToolMessage(
                        content=str(tool_output),
                        tool_call_id=tool_call["id"]
                    ))
            
            # 5. Call the LLM a second time so it can read the tool output and write a final answer
            response = llm_with_tools.invoke(lc_messages)

    except Exception as e:
        # GUARDRAIL 2: Error Fallback
        # If the LLM messes up the JSON or the tool crashes, catch it and try again as a normal chat
        print(f"Tool execution failed, falling back to standard text: {e}")
        response = llm.invoke(lc_messages) 

    reply_text = response.content
    
    # GUARDRAIL 3: Output Cleaning
    # Strip out stray formatting tags (case-insensitive) from free models
    reply_text = re.sub(r"(?i)user safety:\s*\w+\s*", "", reply_text).strip()

    # 6. Save both sides of the exchange
    save_message(thread_id, "user", user_message)
    save_message(thread_id, "bot", reply_text)
    touch_thread(thread_id)

    return {"thread_id": thread_id, "reply": reply_text}


# ---------- Extra functions needed by Mustafa's router ----------

def list_threads(user_id: str) -> list[dict]:
    return get_threads_for_user(user_id)

def rename_thread(thread_id: str, new_title: str) -> bool:
    return update_thread_title(thread_id, new_title)

def delete_thread(thread_id: str) -> bool:
    return crud_delete_thread(thread_id)