from fastapi import FastAPI

app = FastAPI(title="Job Service")

@app.get("/health")
def health():
    return {"status": "ok"}
