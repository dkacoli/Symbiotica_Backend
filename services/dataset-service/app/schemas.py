from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    format: str  # CSV, JSON, PARQUET, etc.

class DatasetChunkUpload(BaseModel):
    chunk_number: int
    total_chunks: int
    chunk_size: int

class DatasetResponse(BaseModel):
    id: str
    user_id: str
    name: str
    status: str
    file_size: float
    format: str
    created_at: datetime
    row_count: Optional[int] = None
    
    class Config:
        from_attributes = True

class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total: int

class AnonymizationRequest(BaseModel):
    dataset_id: str
    fields_to_anonymize: List[str]
    method: str = Field(..., pattern="^(hashing|tokenization|removal)$")
    output_name: str

class AnonymizationResponse(BaseModel):
    anonymization_id: str
    original_dataset_id: str
    status: str
    created_at: datetime

class ValidationError(BaseModel):
    field: str
    error: str