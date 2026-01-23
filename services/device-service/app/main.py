from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from jose import jwt
import os, time

app = FastAPI(title="Device Service")
JWT_SECRET = os.getenv("JWT_SECRET", "dev")

# Day 1: in-memory devices (tomorrow: Postgres)
DEVICES = []  # list of dicts

class RegisterDeviceReq(BaseModel):
    cpu: str
    gpu: str
    ram: str
    bandwidth: str

class HeartbeatReq(BaseModel):
    device_id: str
    cpu_usage: float
    gpu_usage: float
    ram_usage: float
    temp: float

def require_host(auth: str | None):
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = auth.split(" ", 1)[1]
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    if payload.get("role") != "HOST":
        raise HTTPException(403, "HOST role required")
    return payload["sub"]

@app.post("/devices/register")
def register(req: RegisterDeviceReq, authorization: str | None = Header(default=None)):
    email = require_host(authorization)
    device_id = f"dev_{len(DEVICES)+1}"
    DEVICES.append({
        "id": device_id,
        "host_user_id": email,
        "status": "ONLINE",
        "cpu": req.cpu,
        "gpu": req.gpu,
        "ram": req.ram,
        "bandwidth": req.bandwidth,
        "last_heartbeat": time.time(),
        "reputation": 100
    })
    return {"device_id": device_id}

@app.post("/devices/heartbeat")
def heartbeat(req: HeartbeatReq, authorization: str | None = Header(default=None)):
    email = require_host(authorization)
    for d in DEVICES:
        if d["id"] == req.device_id and d["host_user_id"] == email:
            d["last_heartbeat"] = time.time()
            d["status"] = "ONLINE"
            d["metrics"] = req.model_dump()
            return {"ok": True}
    raise HTTPException(404, "Device not found")

@app.get("/devices/me")
def my_devices(authorization: str | None = Header(default=None)):
    email = require_host(authorization)
    now = time.time()
    out = []
    for d in DEVICES:
        if d["host_user_id"] == email:
            # if heartbeat older than 10s mark offline (for Day 1 demo)
            if now - d["last_heartbeat"] > 10:
                d["status"] = "OFFLINE"
            out.append(d)
    return out
