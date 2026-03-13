from fastapi import FastAPI
from app.gateway.routes import router
from app.models.database import init_db

app = FastAPI(title="LLMSentry", description="LLM Observability and Evaluation Platform")

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(router, prefix="/api/v1")