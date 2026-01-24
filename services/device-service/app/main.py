from fastapi import FastAPI
from app.db import engine, Base
from app.routes import router

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

app.include_router(router)
