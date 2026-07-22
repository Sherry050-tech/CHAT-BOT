

from datetime import datetime
from bson import ObjectId
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.database import messages_collection, threads_collection
from app.services.rag_service import search_relevant_chunks

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use the provided context from uploaded "
    "documents if it is relevant to the user's question. If no context "
    "is relevant, just answer normally."
)


async def get_or_create_thread(thread_id: str | None, user_id: str) -> str:
    """Return an existing thread_id, or create a new thread and return its id."""
    if thread_id:
        return thread_id

    result = await threads_collection.insert_one(
        {"user_id": user_id, "title": "New Chat", "created_at": datetime.utcnow()}
    )
    return str(result.inserted_id)


async def get_chat_history(thread_id: str, limit: int = 20) -> list[dict]:
    """Fetch the last `limit` messages in a thread, oldest first."""
    cursor = (
        messages_collection.find({"thread_id": thread_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    history = await cursor.to_list(length=limit)
    return list(reversed(history))


async def save_message(thread_id: str, role: str, content: str):
    await messages_collection.insert_one(
        {
            "thread_id": thread_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow(),
        }
    )


async def generate_reply(thread_id: str, user_message: str, user_id: str = "anon") -> dict:
    """
    Main entry point: takes a message + thread, pulls history + RAG context,
    calls the LLM, saves both messages, and returns the reply.
    """
    thread_id = await get_or_create_thread(thread_id, user_id)

    # 1. Pull relevant chunks from uploaded docs (RAG)
    relevant_chunks = await search_relevant_chunks(thread_id, user_message)
    context_text = "\n\n".join(chunk["chunk_text"] for chunk in relevant_chunks)

    # 2. Pull past conversation history
    history = await get_chat_history(thread_id)

    # 3. Build the LangChain message list
    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    if context_text:
        lc_messages.append(SystemMessage(content=f"Relevant context:\n{context_text}"))

    for msg in history:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        else:
            lc_messages.append(AIMessage(content=msg["content"]))

    lc_messages.append(HumanMessage(content=user_message))

    # 4. Call the LLM
    response = await llm.ainvoke(lc_messages)
    reply_text = response.content

    # 5. Save both sides of the exchange
    await save_message(thread_id, "user", user_message)
    await save_message(thread_id, "assistant", reply_text)

    return {"thread_id": thread_id, "reply": reply_text}