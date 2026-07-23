"""
main.py  -  This file STARTS the whole application.

It does not contain any chat logic or upload logic.
Its only job is to create the app and plug in the routers.
This is the file you point uvicorn at to run the server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat_router
from app.routers import upload_router
from app.routers import auth_router
from app.routers import speech_router

# STEP 1: Create the FastAPI application.
# The title and description show up on the auto-generated docs at /docs
app = FastAPI(
    title="Multimodal Chatbot API",
    description="Backend for our chatbot. Handles chat with memory, and file upload for RAG.",
    version="0.1.0",
)


# STEP 2: Let the frontend talk to this backend.
# The frontend runs on a different port, and browsers block that by default.
# allow_origins=["*"] means "allow everyone" - fine for development only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# STEP 3: Plug in my routers.
# Without these lines the /chat and /upload endpoints would not exist.
app.include_router(chat_router.router)
app.include_router(upload_router.router)
app.include_router(auth_router.router)
app.include_router(speech_router.router)



# STEP 4: A simple health check.
# Visiting http://127.0.0.1:8000/ should return {"status": "ok"}
@app.get("/", tags=["health"])
def root():
    return {"status": "ok"}