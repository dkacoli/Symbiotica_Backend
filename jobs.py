# backend/jobs.py
from fastapi import APIRouter

router = APIRouter(prefix="/jobs")

JOBS = [
    {
        "job_id": "job-1",
        "image": "python:3.11-slim",
        "command": ["python", "-c", "print('hello from job')"],
        "cpu": 1,
        "memory": "512m"
    }
]

@router.get("/next")
def next_job():
    if JOBS:
        return JOBS.pop(0)
    return {}
