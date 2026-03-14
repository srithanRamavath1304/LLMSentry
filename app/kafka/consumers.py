from kafka import KafkaConsumer
from app.models.database import SessionLocal
from app.models.trace import Trace, Evaluation
from google import genai
import json
import os
import uuid
from dotenv import load_dotenv
import pickle
import time

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# evaluator model
evaluator_path = os.path.join(os.path.dirname(__file__), "../../classifier/evaluator_model.pkl")
with open(evaluator_path, "rb") as f:
    evaluator_model = pickle.load(f)

EVALUATOR_TYPE = os.getenv("EVALUATOR_TYPE", "gemini")

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

def evaluate_with_sklearn(prompt: str, response: str) -> dict:
    start = time.time()
    text = prompt + " " + response
    scores = {
        metric: float(model.predict([text])[0])
        for metric, model in evaluator_model.items()
    }
    latency = round((time.time() - start) * 1000, 2)
    print(f"Sklearn evaluation: {latency}ms")
    return {
        "relevance_score": round(min(max(scores["relevance_score"], 0), 1), 4),
        "hallucination_score": round(min(max(scores["hallucination_score"], 0), 1), 4),
        "faithfulness_score": round(min(max(scores["faithfulness_score"], 0), 1), 4),
        "reasoning": f"Sklearn evaluator: overall={round(scores['overall_score'], 4)}"
    }

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

    start = time.time()
    result = httpx.post(
        "http://localhost:11434/api/generate",
        json={"model": "gemma:2b", "prompt": eval_prompt, "stream": False},
        timeout=120.0
    )
    latency = round((time.time() - start) * 1000, 2)
    print(f"Ollama evaluation: {latency}ms")
    data = result.json()
    text = data.get("response", "{}")
    start = text.find("{")
    end = text.rfind("}") + 1
    json_str = text[start:end]
    scores = json.loads(json_str)
    return scores

def evaluate_with_gemini(prompt: str, response: str) -> dict:
    eval_prompt = f"""You are an expert LLM response evaluator. Score this response strictly and objectively.

Question: {prompt}
Response: {response}

Return ONLY valid JSON with NO extra text:
{{
    "relevance_score": 0.0,
    "hallucination_score": 0.0,
    "faithfulness_score": 0.0,
    "reasoning": "brief explanation"
}}

Scoring rules:
- relevance_score: 0.0-1.0, how well response answers the question
- hallucination_score: 0.0-1.0, lower is better, how much false info
- faithfulness_score: 0.0-1.0, how factually consistent the response is
- Use full decimal precision, do not round scores to 2 decimal places
- Example: use 0.73642 not 0.74
- Be strict and vary your scores, don't give everything 0.8+"""
    start = time.time()
    response_obj = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=eval_prompt
    )
    latency = round((time.time() - start) * 1000, 2)
    print(f"Gemini evaluation: {latency}ms")
    text = response_obj.text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    scores = json.loads(text[start:end])
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

            if EVALUATOR_TYPE == "sklearn":
                scores = evaluate_with_sklearn(data["prompt"], data["response"])
            elif EVALUATOR_TYPE == "ollama":
                scores = evaluate_with_ollama(data["prompt"], data["response"])
            else:
                scores = evaluate_with_gemini(data["prompt"], data["response"])

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