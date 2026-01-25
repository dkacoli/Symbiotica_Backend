# app/routes.py (or wherever your router is)

from __future__ import annotations

import os
from typing import List, Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.anonymizer import AnonymizationEngine

router = APIRouter(prefix="/api/v1/anonymize", tags=["anonymization"])
engine = AnonymizationEngine()

DATASET_SERVICE_URL = os.getenv("DATASET_SERVICE_URL", "http://dataset-service:8000")

# In-memory status store (OK for dev). For production: put this in Postgres/Redis.
STATUS: Dict[str, Dict[str, Any]] = {}


class AnonymizeRequest(BaseModel):
    anonymization_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    file_format: str = Field(..., min_length=1)
    fields_to_anonymize: List[str] = Field(default_factory=list)
    method: str = Field(..., min_length=1)  # "hash" | "tokenize" | "remove" (your engine decides)


async def _download_dataset_bytes(client: httpx.AsyncClient, dataset_id: str) -> bytes:
    """
    Requires dataset-service endpoint:
      GET /api/v1/datasets/{dataset_id}/download
    returning raw file bytes (ideally DECRYPTED already inside dataset-service).
    """
    url = f"{DATASET_SERVICE_URL}/api/v1/datasets/{dataset_id}/download"
    r = await client.get(url, timeout=120.0)
    r.raise_for_status()
    return r.content


async def _upload_anonymized_bytes(
    client: httpx.AsyncClient,
    parent_dataset_id: str,
    file_format: str,
    anonymized_bytes: bytes,
    anonymization_id: str,
) -> Dict[str, Any]:
    """
    Requires dataset-service endpoint:
      POST /api/v1/datasets/anonymized
    that:
      - creates a new dataset row (output dataset)
      - stores bytes in S3/MinIO (encrypted at rest)
      - returns output dataset info (id, name, status)
    """
    url = f"{DATASET_SERVICE_URL}/api/v1/datasets/anonymized"

    # multipart upload
    files = {
        "file": ("anonymized.bin", anonymized_bytes, "application/octet-stream"),
    }
    data = {
        "parent_dataset_id": parent_dataset_id,
        "format": file_format,
        "name": f"{parent_dataset_id}_anonymized",
        "anonymization_id": anonymization_id,
    }

    r = await client.post(url, data=data, files=files, timeout=300.0)
    r.raise_for_status()
    return r.json()


async def process_anonymization(
    anonymization_id: str,
    dataset_id: str,
    file_format: str,
    fields_to_anonymize: List[str],
    method: str,
) -> None:
    STATUS[anonymization_id] = {
        "anonymization_id": anonymization_id,
        "status": "processing",
        "input_dataset_id": dataset_id,
    }

    try:
        async with httpx.AsyncClient() as client:
            # 1) Optional: confirm dataset exists
            info_url = f"{DATASET_SERVICE_URL}/api/v1/datasets/{dataset_id}"
            info_resp = await client.get(info_url, timeout=30.0)
            info_resp.raise_for_status()

            # 2) Download dataset bytes
            raw_bytes = await _download_dataset_bytes(client, dataset_id)

            # 3) Anonymize (your engine must return bytes)
            anonymized_bytes = engine.anonymize_dataset(
                raw_bytes,
                file_format,
                fields_to_anonymize,
                method,
            )

            # 4) Upload anonymized result so it is stored + appears in catalog
            out = await _upload_anonymized_bytes(
                client=client,
                parent_dataset_id=dataset_id,
                file_format=file_format,
                anonymized_bytes=anonymized_bytes,
                anonymization_id=anonymization_id,
            )

            STATUS[anonymization_id] = {
                "anonymization_id": anonymization_id,
                "status": "completed",
                "input_dataset_id": dataset_id,
                "output": out,  # includes output dataset id
            }

    except httpx.HTTPStatusError as e:
        STATUS[anonymization_id] = {
            "anonymization_id": anonymization_id,
            "status": "failed",
            "input_dataset_id": dataset_id,
            "error": f"Dataset-service error: {e.response.status_code} {e.response.text[:500]}",
        }
    except Exception as e:
        STATUS[anonymization_id] = {
            "anonymization_id": anonymization_id,
            "status": "failed",
            "input_dataset_id": dataset_id,
            "error": str(e),
        }


@router.post("/process")
async def process(request: AnonymizeRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        process_anonymization,
        request.anonymization_id,
        request.dataset_id,
        request.file_format,
        request.fields_to_anonymize,
        request.method,
    )
    return {"anonymization_id": request.anonymization_id, "status": "processing_started"}


@router.get("/status/{anonymization_id}")
def status(anonymization_id: str):
    return STATUS.get(anonymization_id, {"anonymization_id": anonymization_id, "status": "unknown"})


@router.get("/health")
def health():
    return {"status": "healthy"}
