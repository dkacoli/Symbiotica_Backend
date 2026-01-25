from fastapi import FastAPI
from app.db import engine, Base
from app.routes import router

app = FastAPI(
    title="Dataset Storage Service",
    description="Secure dataset upload, storage, and anonymization",
    version="1.0.0",
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "healthy"}