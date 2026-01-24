from datetime import datetime
from app.models import Device, DeviceStatus
from app.exceptions import DeviceNotFoundException

class DeviceService:
    def __init__(self, repo):
        self.repo = repo

    def register_device(self, db, host_id, data):
        device = Device(
            host_user_id=host_id,
            cpu=data.cpu,
            gpu=data.gpu,
            ram=data.ram,
            bandwidth=data.bandwidth,
            status=DeviceStatus.ONLINE
        )
        return self.repo.create(db, device)

    def heartbeat(self, db, device: Device, status):
        device.status = status
        device.last_heartbeat = datetime.utcnow()
        db.commit()
        return device
