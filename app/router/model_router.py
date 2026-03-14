import redis
import os
import json
from dotenv import load_dotenv
import httpx
import pickle
import time

load_dotenv()

r = redis.from_url(os.getenv("REDIS_URL"))

COST_PER_1K_TOKENS = {
    "gemini": 0.00015,
    "ollama": 0.0
}

CLASSIFIER_TYPE = os.getenv("COMPLEXITY_CLASSIFIER", "ollama")

complexity_classifier = None
if CLASSIFIER_TYPE == "sklearn":
    model_path = os.path.join(os.path.dirname(__file__), "../../classifier/quality_classifier.pkl")
    with open(model_path, "rb") as f:
        complexity_classifier = pickle.load(f)

def classify_complexity(prompt: str) -> str:
    start = time.time()
    
    if CLASSIFIER_TYPE == "sklearn":
        try:
            prediction = complexity_classifier.predict([prompt + " "])[0]
            result = "complex" if prediction == 1 else "simple"
            print(f"Sklearn classification: {result} in {round((time.time()-start)*1000, 2)}ms")
            return result
        except Exception as e:
            print(f"Sklearn classifier failed: {e}")
            return "simple"
    else:
        try:
            response = httpx.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma:2b",
                    "prompt": f"""Classify this query as 'simple' or 'complex'.
Simple = short factual questions with a single answer.
Complex = explanations, analysis, comparisons, or detailed descriptions.
Reply with ONLY one word: simple or complex.
Query: {prompt}""",
                    "stream": False
                },
                timeout=30.0
            )
            result = response.json().get("response", "").strip().lower()
            result = "complex" if "complex" in result else "simple"
            print(f"Ollama classification: {result} in {round((time.time()-start)*1000, 2)}ms")
            return result
        except Exception as e:
            print(f"Ollama classifier failed: {e}")
            return "simple"

def get_routing_decision(prompt: str) -> dict:
    cache_key = f"route:{hash(prompt)}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    complexity = classify_complexity(prompt)

    if complexity == "simple":
        decision = {
            "provider": "ollama",
            "model": "gemma:2b",
            "complexity": complexity,
            "reason": "Simple query routed to local model to save cost"
        }
    else:
        decision = {
            "provider": "gemini",
            "model": "gemini-2.5-flash-lite",
            "complexity": complexity,
            "reason": "Complex query routed to Gemini for quality"
        }

    r.setex(cache_key, 3600, json.dumps(decision))
    return decision

def calculate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
    rate = COST_PER_1K_TOKENS.get(provider, 0)
    return ((input_tokens + output_tokens) / 1000) * rate