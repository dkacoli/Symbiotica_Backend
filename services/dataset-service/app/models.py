from sqlalchemy import Column, String, Integer, Float, Enum, DateTime, Boolean, JSON
from app.db import Base
from datetime import datetime
import enum
import uuid

class DatasetStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PROCESSING = "PROCESSING"

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(Enum(DatasetStatus), default=DatasetStatus.UPLOADING)
    file_size = Column(Float)  # in bytes
    file_count = Column(Integer, default=0)
    s3_key = Column(String, unique=True)
    checksum = Column(String)  # SHA256 hash
    is_encrypted = Column(Boolean, default=True)
    format = Column(String)  # CSV, JSON, PARQUET, etc.
    schema = Column(JSON, nullable=True)  # Column names and types
    row_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column(JSON, nullable=True)

class DatasetChunk(Base):
    __tablename__ = "dataset_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, index=True)
    chunk_number = Column(Integer)
    chunk_size = Column(Float)
    s3_key = Column(String, unique=True)
    checksum = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_encrypted = Column(Boolean, default=True)

class AnonymizedDataset(Base):
    __tablename__ = "anonymized_datasets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_dataset_id = Column(String, index=True)
    user_id = Column(String, index=True)
    anonymized_fields = Column(JSON)  # List of anonymized field names
    anonymization_method = Column(String)  # hashing, tokenization, removal
    output_dataset_id = Column(String)  # Reference to created dataset
    s3_key = Column(String, unique=True)
    status = Column(String, default="PROCESSING")  # PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)