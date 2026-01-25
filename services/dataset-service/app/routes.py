from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.schemas import (
    DatasetCreate,
    DatasetResponse,
    DatasetListResponse,
    AnonymizationRequest,
    ValidationError,
)
from app.service import DatasetService
from typing import List, Optional

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])
service = DatasetService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_id_from_token() -> str:
    # This will be replaced with actual JWT verification
    return "user_1"

@router.post("/create", response_model=dict)
def create_dataset(
    name: str = Form(...),
    format: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id_from_token),
):
    """Create a new dataset"""
    try:
        data = DatasetCreate(name=name, format=format, description=description)
        dataset = service.create_dataset(db, user_id, data)
        return {
            "id": dataset.id,
            "name": dataset.name,
            "status": dataset.status,
            "format": dataset.format,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload/{dataset_id}")
def upload_chunk(
    dataset_id: str,
    chunk_number: int = Form(...),
    total_chunks: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id_from_token),
):
    """Upload a dataset chunk"""
    try:
        # Validate file size (max 100MB per chunk)
        file_data = file.file.read()
        if len(file_data) > 100 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Chunk too large (max 100MB)")
        
        result = service.upload_chunk(
            db,
            dataset_id,
            file_data,
            chunk_number,
            total_chunks,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id_from_token),
):
    """Get dataset information"""
    try:
        info = service.get_dataset_info(db, dataset_id)
        return info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("", response_model=DatasetListResponse)
def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id_from_token),
):
    """List all datasets for the user"""
    result = service.list_user_datasets(db, user_id, skip, limit)
    return result

@router.post("/anonymize")
def anonymize_dataset(
    request: AnonymizationRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id_from_token),
):
    """Request dataset anonymization"""
    try:
        # Validate the original dataset exists
        dataset = service.repo.get_dataset(db, request.dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Create anonymization job
        anon_dataset = service.repo.create_anonymized_dataset(
            db,
            request.dataset_id,
            user_id,
            request.fields_to_anonymize,
            request.method,
        )
        
        return {
            "anonymization_id": anon_dataset.id,
            "status": anon_dataset.status,
            "created_at": anon_dataset.created_at,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/anonymize/{anonymization_id}")
def get_anonymization_status(
    anonymization_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id_from_token),
):
    """Get anonymization job status"""
    anon_dataset = service.repo.get_anonymized_dataset(db, anonymization_id)
    if not anon_dataset:
        raise HTTPException(status_code=404, detail="Anonymization job not found")
    
    return {
        "id": anon_dataset.id,
        "status": anon_dataset.status,
        "original_dataset_id": anon_dataset.original_dataset_id,
        "anonymized_fields": anon_dataset.anonymized_fields,
        "method": anon_dataset.anonymization_method,
    }