from fastapi import FastAPI

app = FastAPI(title="Job Service")

JOBS = [
    {
        "job_id": "job-1",
        "image": "python:3.11-slim",
        "command": ["python", "-c", "print('Hello from job')"],
        "cpu": 1,
        "memory": "512m",
        "status": "PENDING"
    }
]

@app.get("/jobs/pending")
def pending_jobs():
    return [j for j in JOBS if j["status"] == "PENDING"]

@app.post("/jobs/{job_id}/assign")
def assign(job_id: str):
    for j in JOBS:
        if j["job_id"] == job_id:
            j["status"] = "ASSIGNED"
            return j
