from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
import os
import time

app = FastAPI(title="IAM Service")

JWT_SECRET = os.getenv("JWT_SECRET", "dev")
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Day 1: keep users in memory (tomorrow: move to Postgres)
USERS = {}  # email -> {password_hash, role}

class RegisterReq(BaseModel):
    email: str
    password: str
    role: str  # GUEST or HOST

class LoginReq(BaseModel):
    email: str
    password: str

def make_token(email: str, role: str, minutes: int):
    now = int(time.time())
    payload = {"sub": email, "role": role, "iat": now, "exp": now + minutes * 60}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@app.post("/auth/register")
def register(req: RegisterReq):
    if req.email in USERS:
        raise HTTPException(400, "User already exists")
    if req.role not in ["GUEST", "HOST", "ADMIN"]:
        raise HTTPException(400, "Invalid role")
    USERS[req.email] = {"password_hash": pwd.hash(req.password), "role": req.role}
    return {"ok": True}

@app.post("/auth/login")
def login(req: LoginReq):
    user = USERS.get(req.email)
    if not user or not pwd.verify(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    access = make_token(req.email, user["role"], minutes=30)
    refresh = make_token(req.email, user["role"], minutes=60*24*7)
    return {"access_token": access, "refresh_token": refresh, "role": user["role"]}
