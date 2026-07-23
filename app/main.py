import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import chat_router
from app.routers import upload_router
from app.routers import auth_router
from app.routers import speech_router

app = FastAPI(
    title="Multimodal Chatbot API",
    description="Backend for our chatbot. Handles chat with memory, and file upload for RAG.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router.router)
app.include_router(upload_router.router)
app.include_router(auth_router.router)
app.include_router(speech_router.router)

# --- THE FIX ---
# This gets the exact folder where main.py is currently sitting
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# This joins it with the frontend folder sitting right next to it
FRONTEND_DIR = os.path.join(CURRENT_DIR, "frontend")

# Mount the frontend
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")