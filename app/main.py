"""
main.py  -  This file STARTS the whole application.

It does not contain any chat logic or upload logic.
Its only job is to create the app and plug in the routers.
This is the file you point uvicorn at to run the server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import my two router files (the ones I wrote myself)
from app.routers import chat_router
from app.routers import upload_router


# STEP 1: Create the FastAPI application.
# The title and description below show up on the auto-generated docs page at /docs
app = FastAPI(
    title="Multimodal Chatbot API",
    description="Backend for our chatbot. Handles chat with memory, and file upload for RAG.",
    version="0.1.0",
)


# STEP 2: Allow the frontend to talk to this backend.
# The frontend usually runs on a different port (like 3000) than the backend (8000).
# Browsers block that by default, so CORS middleware tells the browser "it's fine, allow it".
# Note: allow_origins=["*"] means "allow everyone". Fine for development, tighten it later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# STEP 3: Plug in my routers.
# Each router is a group of endpoints living in its own file.
# Without these two lines, the /chat and /upload endpoints would not exist.
app.include_router(chat_router.router)
app.include_router(upload_router.router)


# STEP 4: A simple health check endpoint.
# Visiting http://127.0.0.1:8000/ should return {"status": "ok"}
# This is just a quick way to confirm the server is alive.
@app.get("/", tags=["health"])
def root():
    return {"status": "ok"}