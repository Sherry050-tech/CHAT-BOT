from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models import User
from app.crud import create_user
from app.database import users_collection
from passlib.context import CryptContext
import numpy as np

router = APIRouter(tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def euclidean_distance(a, b):
    a, b = np.array(a), np.array(b)
    return np.linalg.norm(a - b)


class SignupRequest(BaseModel):
    username: str
    email: str | None = None
    password: str
    face_embedding: list[float]


class SigninUsernameRequest(BaseModel):
    username: str
    password: str


class SigninFaceRequest(BaseModel):
    face_embedding: list[float]


FACE_MATCH_THRESHOLD = 0.42


@router.post("/signup")
def signup(request: SignupRequest):
    existing = users_collection.find_one({"username": request.username})
    if existing:
        raise HTTPException(status_code=400, detail="username already taken")

    hashed_password = pwd_context.hash(request.password)
    user = User(
        username=request.username,
        email=request.email,
        password_hash=hashed_password,
        face_embedding=request.face_embedding,
    )
    create_user(user)

    return {"status": "signed up", "username": user.username, "user_id": user.id}


@router.post("/signin/username")
def signin_username(request: SigninUsernameRequest):
    user = users_collection.find_one({"username": request.username})
    if not user or not pwd_context.verify(request.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="incorrect username or password")

    return {"status": "signed in", "username": user["username"], "user_id": user["id"]}


@router.post("/signin/face")
def signin_face(request: SigninFaceRequest):
    all_users = list(users_collection.find({"face_embedding": {"$ne": None}}))

    if not all_users:
        raise HTTPException(status_code=404, detail="no registered faces found")

    best_match = None
    best_distance = float("inf")

    for user in all_users:
        distance = euclidean_distance(request.face_embedding, user["face_embedding"])
        if distance < best_distance:
            best_distance = distance
            best_match = user

    if best_distance > FACE_MATCH_THRESHOLD:
        raise HTTPException(status_code=404, detail="no matching face found")

    return {"status": "signed in", "username": best_match["username"], "user_id": best_match["id"], "match_distance": best_distance}