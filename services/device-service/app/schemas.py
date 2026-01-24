from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import DeviceStatus

class DeviceRegister(BaseModel):
    cpu: str
    gpu: Optional[str]
    ram: float
    bandwidth: float

class Heartbeat(BaseModel):
    status: DeviceStatus

class DeviceResponse(BaseModel):
    id: int
    status: DeviceStatus
    last_heartbeat: datetime

    class Config:
        from_attributes = True
