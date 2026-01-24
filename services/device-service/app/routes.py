from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.schemas import DeviceRegister, Heartbeat
from app.repository import SqlDeviceRepository
from app.service import DeviceService

router = APIRouter()
service = DeviceService(SqlDeviceRepository())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/devices/register")
def register_device(data: DeviceRegister, db: Session = Depends(get_db)):
    host_id = 1  # later from JWT
    return service.register_device(db, host_id, data)

@router.post("/devices/heartbeat/{device_id}")
def heartbeat(device_id: int, hb: Heartbeat, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    return service.heartbeat(db, device, hb.status)
