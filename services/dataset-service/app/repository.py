from sqlalchemy.orm import Session
from app.models import Dataset, DatasetChunk, AnonymizedDataset, DatasetStatus
from app.schemas import DatasetCreate
from typing import Optional, List
import uuid

class DatasetRepository:
    """Database operations for datasets"""
    
    @staticmethod
    def create_dataset(db: Session, user_id: str, data: DatasetCreate) -> Dataset:
        dataset = Dataset(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data.name,
            description=data.description,
            format=data.format,
            status=DatasetStatus.UPLOADING,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset
    
    @staticmethod
    def update_dataset(db: Session, dataset_id: str, **kwargs) -> Dataset:
        db.query(Dataset).filter(Dataset.id == dataset_id).update(kwargs)
        db.commit()
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    @staticmethod
    def get_dataset(db: Session, dataset_id: str) -> Optional[Dataset]:
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    @staticmethod
    def list_datasets(db: Session, user_id: str, skip: int = 0, limit: int = 10) -> tuple[List[Dataset], int]:
        query = db.query(Dataset).filter(Dataset.user_id == user_id)
        total = query.count()
        datasets = query.offset(skip).limit(limit).all()
        return datasets, total
    
    @staticmethod
    def create_chunk(
        db: Session,
        dataset_id: str,
        chunk_number: int,
        chunk_size: float,
        s3_key: str,
        checksum: str,
    ) -> DatasetChunk:
        chunk = DatasetChunk(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            chunk_number=chunk_number,
            chunk_size=chunk_size,
            s3_key=s3_key,
            checksum=checksum,
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        return chunk
    
    @staticmethod
    def get_chunks(db: Session, dataset_id: str) -> List[DatasetChunk]:
        return db.query(DatasetChunk).filter(DatasetChunk.dataset_id == dataset_id).order_by(DatasetChunk.chunk_number).all()
    
    @staticmethod
    def create_anonymized_dataset(
        db: Session,
        original_dataset_id: str,
        user_id: str,
        anonymized_fields: list,
        method: str,
    ) -> AnonymizedDataset:
        anon_dataset = AnonymizedDataset(
            id=str(uuid.uuid4()),
            original_dataset_id=original_dataset_id,
            user_id=user_id,
            anonymized_fields=anonymized_fields,
            anonymization_method=method,
            status="PROCESSING",
        )
        db.add(anon_dataset)
        db.commit()
        db.refresh(anon_dataset)
        return anon_dataset
    
    @staticmethod
    def get_anonymized_dataset(db: Session, anonymization_id: str) -> Optional[AnonymizedDataset]:
        return db.query(AnonymizedDataset).filter(AnonymizedDataset.id == anonymization_id).first()