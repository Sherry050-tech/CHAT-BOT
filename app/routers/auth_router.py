from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models import User
from app.crud import create_user
from app.database import users_collection
import numpy as np

router = APIRouter(tags=["auth"])


def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


class SignupRequest(BaseModel):
    username: str
    email: str | None = None
    face_embedding: list[float]


class SigninUsernameRequest(BaseModel):
    username: str


class SigninFaceRequest(BaseModel):
    face_embedding: list[float]


FACE_MATCH_THRESHOLD = 0.6


@router.post("/signup")
def signup(request: SignupRequest):
    existing = users_collection.find_one({"username": request.username})
    if existing:
        raise HTTPException(status_code=400, detail="username already taken")

    user = User(username=request.username, email=request.email, face_embedding=request.face_embedding)
    create_user(user)

    return {"status": "signed up", "username": user.username, "user_id": user.id}


@router.post("/signin/username")
def signin_username(request: SigninUsernameRequest):
    user = users_collection.find_one({"username": request.username})
    if not user:
        raise HTTPException(status_code=404, detail="username not found")

    return {"status": "signed in", "username": user["username"], "user_id": user["id"]}


@router.post("/signin/face")
def signin_face(request: SigninFaceRequest):
    all_users = list(users_collection.find({"face_embedding": {"$ne": None}}))

    if not all_users:
        raise HTTPException(status_code=404, detail="no registered faces found")

    best_match = None
    best_score = -1

    for user in all_users:
        score = cosine_similarity(request.face_embedding, user["face_embedding"])
        if score > best_score:
            best_score = score
            best_match = user

    if best_score < FACE_MATCH_THRESHOLD:
        raise HTTPException(status_code=404, detail="no matching face found")

    return {"status": "signed in", "username": best_match["username"], "user_id": best_match["id"], "match_score": best_score}