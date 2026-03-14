from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import get_db
from app.router.model_router import get_routing_decision, calculate_cost
from app.gateway.llm_caller import call_llm
from app.kafka.producer import publish_trace, publish_evaluation_request
from app.models.trace import Trace
from datetime import datetime
import uuid

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str

@router.post("/chat")
async def chat(request: PromptRequest, db: Session = Depends(get_db)):
    prompt = request.prompt

    routing = get_routing_decision(prompt)

    result = call_llm(routing["provider"], prompt)

    cost = calculate_cost(
        routing["provider"],
        result["input_tokens"],
        result["output_tokens"]
    )

    trace = {
        "id": str(uuid.uuid4()),
        "prompt": prompt,
        "response": result["response"],
        "provider": result["provider"],
        "model": result["model"],
        "latency_ms": result["latency_ms"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "cost_usd": cost,
        "complexity": routing["complexity"],
        "created_at": datetime.utcnow().isoformat()
    }

    publish_trace(trace)
    publish_evaluation_request(trace)

    return {
        "response": result["response"],
        "provider": result["provider"],
        "model": result["model"],
        "latency_ms": result["latency_ms"],
        "cost_usd": cost,
        "complexity": routing["complexity"]
    }