import hashlib
import csv
import json
from typing import List, Optional, BinaryIO
from sqlalchemy.orm import Session
from app.models import Dataset, DatasetStatus
from app.schemas import DatasetCreate, AnonymizationRequest
from app.repository import DatasetRepository
from app.storage import S3StorageService
from app.encryption import DatasetEncryption
import pandas as pd
import io

class DatasetService:
    """Business logic for dataset management"""
    
    def __init__(self):
        self.storage = S3StorageService()
        self.encryption = DatasetEncryption()
        self.repo = DatasetRepository()
    
    def create_dataset(self, db: Session, user_id: str, data: DatasetCreate) -> Dataset:
        """Create a new dataset record"""
        return self.repo.create_dataset(db, user_id, data)
    
    def validate_file_format(self, format: str, file_data: bytes) -> bool:
        """Validate file format"""
        allowed_formats = ["CSV", "JSON", "PARQUET", "EXCEL"]
        if format.upper() not in allowed_formats:
            return False
        
        try:
            if format.upper() == "CSV":
                df = pd.read_csv(io.BytesIO(file_data), nrows=5)
                return True
            elif format.upper() == "JSON":
                json.loads(file_data.decode())
                return True
            elif format.upper() == "PARQUET":
                pd.read_parquet(io.BytesIO(file_data))
                return True
            return True
        except Exception:
            return False
    
    def validate_file_size(self, file_size: int, max_size_mb: int = 500) -> bool:
        """Validate file doesn't exceed max size"""
        max_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_bytes
    
    def upload_chunk(
        self,
        db: Session,
        dataset_id: str,
        file_data: bytes,
        chunk_number: int,
        total_chunks: int,
    ) -> dict:
        """Upload a chunk of a dataset"""
        dataset = self.repo.get_dataset(db, dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")
        
        # Encrypt the chunk
        encrypted_data = self.encryption.encrypt_file(file_data, dataset_id)
        
        # Upload to S3
        s3_key, checksum = self.storage.upload_chunk(encrypted_data, dataset_id, chunk_number)
        
        # Store chunk metadata
        self.repo.create_chunk(
            db,
            dataset_id,
            chunk_number,
            len(file_data),
            s3_key,
            checksum,
        )
        
        # If all chunks uploaded, mark as completed
        if chunk_number == total_chunks:
            self.repo.update_dataset(
                db,
                dataset_id,
                status=DatasetStatus.COMPLETED,
            )
        
        return {
            "dataset_id": dataset_id,
            "chunk_number": chunk_number,
            "status": "uploaded",
            "checksum": checksum,
        }
    
    def get_dataset_info(self, db: Session, dataset_id: str) -> dict:
        """Get dataset information"""
        dataset = self.repo.get_dataset(db, dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")
        
        return {
            "id": dataset.id,
            "name": dataset.name,
            "status": dataset.status,
            "format": dataset.format,
            "size": dataset.file_size,
            "created_at": dataset.created_at,
        }
    
    def list_user_datasets(self, db: Session, user_id: str, skip: int = 0, limit: int = 10) -> dict:
        """List all datasets for a user"""
        datasets, total = self.repo.list_datasets(db, user_id, skip, limit)
        return {
            "datasets": [
                {
                    "id": d.id,
                    "name": d.name,
                    "status": d.status,
                    "format": d.format,
                    "size": d.file_size,
                    "created_at": d.created_at,
                }
                for d in datasets
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
        }