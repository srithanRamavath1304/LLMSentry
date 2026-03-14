from fastapi import FastAPI
from app.gateway.routes import router as gateway_router
from app.dashboard.routes import router as dashboard_router
from app.models.database import init_db

app = FastAPI(title="LLMSentry", description="LLM Observability and Evaluation Platform")

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(gateway_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/dashboard")