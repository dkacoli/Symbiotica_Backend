import requests
from fastapi import FastAPI

DEVICE_SERVICE = "http://localhost:8001"
JOB_SERVICE = "http://localhost:8002"

app = FastAPI(title="Scheduler")

@app.post("/schedule")
def schedule():
    devices = requests.get(f"{DEVICE_SERVICE}/devices").json()
    jobs = requests.get(f"{JOB_SERVICE}/jobs/pending").json()

    if not devices or not jobs:
        return {"status": "nothing to schedule"}

    device_id = list(devices.keys())[0]
    job = jobs[0]

    requests.post(f"{JOB_SERVICE}/jobs/{job['job_id']}/assign")

    return {
        "job_id": job["job_id"],
        "assigned_to": device_id
    }
