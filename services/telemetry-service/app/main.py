from fastapi import FastAPI

app = FastAPI(title="Telemetry Service")

@app.get("/health")
def health():
    return {"status": "ok"}
