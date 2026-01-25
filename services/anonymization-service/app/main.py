from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="Anonymization Service",
    description="Dataset anonymization with multiple strategies",
    version="1.0.0",
)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "healthy"}