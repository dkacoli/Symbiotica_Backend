from fastapi import FastAPI
from time import time

app = FastAPI(title="Device Service")

DEVICES = {}

@app.post("/devices/register")
def register(device: dict):
    DEVICES[device["device_id"]] = {
        **device,
        "status": "ONLINE",
        "last_seen": time()
    }
    return {"status": "registered"}

@app.post("/devices/heartbeat")
def heartbeat(data: dict):
    if data["device_id"] in DEVICES:
        DEVICES[data["device_id"]]["last_seen"] = time()
        DEVICES[data["device_id"]]["status"] = "ONLINE"
    return {"ok": True}

@app.get("/devices")
def list_devices():
    return DEVICES
