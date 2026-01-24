from sqlalchemy import Column, Integer, String, Float, Enum, DateTime
from app.db import Base
import enum
from datetime import datetime

class DeviceStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    BUSY = "BUSY"

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    host_user_id = Column(Integer, index=True)
    cpu = Column(String)
    gpu = Column(String)
    ram = Column(Float)
    bandwidth = Column(Float)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
