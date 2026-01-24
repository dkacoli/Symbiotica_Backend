from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from app.models import Device

class DeviceRepository(ABC):
    @abstractmethod
    def create(self, db: Session, device: Device): pass

    @abstractmethod
    def get_by_host(self, db: Session, host_id: int): pass

class SqlDeviceRepository(DeviceRepository):
    def create(self, db, device):
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    def get_by_host(self, db, host_id):
        return db.query(Device).filter(Device.host_user_id == host_id).all()
