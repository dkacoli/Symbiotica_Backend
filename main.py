# backend/main.py
from fastapi import FastAPI
from devices import router as devices_router
from jobs import router as jobs_router

app = FastAPI(title="Symbiotica MVP")

#app.include_router(devices_router)
#app.include_router(jobs_router)

@app.get("/")
def root():
    return {"status": "backend alive"}
    