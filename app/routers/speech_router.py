from fastapi import APIRouter, UploadFile, File, HTTPException
from groq import Groq
import os

router = APIRouter(tags=["speech"])
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    if not audio_bytes or len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Recording too short, please try again.")

    try:
        transcription = client.audio.transcriptions.create(
            file=(file.filename, audio_bytes),
            model="whisper-large-v3",
        )
        return {"text": transcription.text}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not process audio, please try again.")