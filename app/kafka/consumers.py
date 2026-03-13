from kafka import KafkaConsumer
from app.models.database import SessionLocal
from app.models.trace import Trace, Evaluation
from google import genai
import json
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def run_trace_consumer():
    consumer = KafkaConsumer(
        "llm.traces",
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="trace-consumer-group",
        auto_offset_reset="earliest"
    )
    print("Trace consumer started...")
    db = SessionLocal()
    for message in consumer:
        try:
            data = message.value
            trace = Trace(
                id=data["id"],
                prompt=data["prompt"],
                response=data["response"],
                provider=data["provider"],
                model=data["model"],
                latency_ms=data["latency_ms"],
                input_tokens=data["input_tokens"],
                output_tokens=data["output_tokens"],
                cost_usd=data["cost_usd"],
                complexity=data["complexity"],
            )
            db.add(trace)
            db.commit()
            print(f"Trace saved: {data['id']}")
        except Exception as e:
            print(f"Trace consumer error: {e}")
            db.rollback()

def evaluate_with_ollama(prompt: str, response: str) -> dict:
    import httpx
    eval_prompt = f"""You are an expert evaluator. Score this LLM response on three metrics.

Question: {prompt}
Response: {response}

Return ONLY valid JSON like this:
{{
    "relevance_score": 0.9,
    "hallucination_score": 0.1,
    "faithfulness_score": 0.85,
    "reasoning": "Brief explanation"
}}

Scores must be between 0 and 1. hallucination_score: lower is better."""

    result = httpx.post(
        "http://localhost:11434/api/generate",
        json={"model": "gemma:2b", "prompt": eval_prompt, "stream": False},
        timeout=120.0
    )
    data = result.json()
    text = data.get("response", "{}")
    # extract JSON from response
    start = text.find("{")
    end = text.rfind("}") + 1
    json_str = text[start:end]
    scores = json.loads(json_str)
    return scores

def run_evaluation_consumer():
    consumer = KafkaConsumer(
        "llm.evaluations",
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="evaluation-consumer-group",
        auto_offset_reset="earliest"
    )
    print("Evaluation consumer started...")
    db = SessionLocal()
    for message in consumer:
        try:
            data = message.value
            scores = evaluate_with_ollama(data["prompt"], data["response"])
            overall = (
                scores["relevance_score"] +
                (1 - scores["hallucination_score"]) +
                scores["faithfulness_score"]
            ) / 3

            evaluation = Evaluation(
                id=str(uuid.uuid4()),
                trace_id=data["id"],
                relevance_score=scores["relevance_score"],
                hallucination_score=scores["hallucination_score"],
                faithfulness_score=scores["faithfulness_score"],
                overall_score=round(overall, 3),
                judge_reasoning=scores.get("reasoning", "")
            )
            db.add(evaluation)
            db.commit()
            print(f"Evaluation saved for trace: {data['id']}")
        except Exception as e:
            print(f"Evaluation consumer error: {e}")
            db.rollback()