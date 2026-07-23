"""
main.py  -  This file STARTS the whole application.

It does not contain any chat logic or upload logic.
Its only job is to create the app and plug in the routers.
This is the file you point uvicorn at to run the server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # <-- NEW: Import this to serve your frontend folder

from app.routers import chat_router
from app.routers import upload_router
from app.routers import auth_router
from app.routers import speech_router

# STEP 1: Create the FastAPI application.
app = FastAPI(
    title="Multimodal Chatbot API",
    description="Backend for our chatbot. Handles chat with memory, and file upload for RAG.",
    version="0.1.0",
)

# STEP 2: Let the frontend talk to this backend.
# We changed this to ["*"] so both your local laptop and Railway can connect without CORS blocking them.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STEP 3: Plug in my routers.
# IMPORTANT: These must stay ABOVE the frontend mount so your API links don't break.
app.include_router(chat_router.router)
app.include_router(upload_router.router)
app.include_router(auth_router.router)
app.include_router(speech_router.router)

# STEP 4: Serve the whole visual frontend (including all subfolders)!
# Placing this at the VERY BOTTOM is crucial. 
# html=True tells FastAPI to serve 'index.html' automatically on the main URL.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")