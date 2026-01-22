# backend/devices.py
from fastapi import APIRouter
from time import time

router = APIRouter(prefix="/devices")

DEVICES = {}

@router.post("/register")
def register_device(device: dict):
    DEVICES[device["device_id"]] = {
        **device,
        "last_seen": time(),
        "status": "ONLINE"
    }
    return {"status": "registered"}

@router.post("/heartbeat")
def heartbeat(data: dict):
    if data["device_id"] in DEVICES:
        DEVICES[data["device_id"]]["last_seen"] = time()
        DEVICES[data["device_id"]]["status"] = "ONLINE"
    return {"ok": True}

@router.get("/")
def list_devices():
    return DEVICES
