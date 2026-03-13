import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

r = redis.from_url(os.getenv("REDIS_URL"))

SIMPLE_KEYWORDS = [
    "what is", "who is", "capital of", "how many", "when did",
    "define", "meaning of", "translate", "calculate", "what are"
]

COMPLEX_KEYWORDS = [
        "explain", "describe", "compare", "difference", "analyze",
        "elaborate", "discuss", "how does", "why does", "what are the",
        "architectural", "in detail", "essay", "detailed", "summarize"
    ]

COST_PER_1K_TOKENS = {
    "gemini": 0.00015,
    "ollama": 0.0
}

def classify_complexity(prompt: str) -> str:
    prompt_lower = prompt.lower()

    for keyword in COMPLEX_KEYWORDS:
        if keyword in prompt_lower:
            return "complex"

    for keyword in SIMPLE_KEYWORDS:
        if keyword in prompt_lower:
            return "simple"

    if len(prompt.split()) < 15:
        return "simple"

    return "complex"

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
        # decision = {
        #     "provider": "gemini",
        #     "model": "gemini-1.5-flash",
        #     "complexity": complexity,
        #     "reason": "Complex query routed to Gemini for quality"
        # }
        decision = {
            "provider": "ollama",
            "model": "gemma:2b",
            "complexity": complexity,
            "reason": "Complex query routed to Ollama"
        }

    r.setex(cache_key, 3600, json.dumps(decision))
    return decision

def calculate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
    rate = COST_PER_1K_TOKENS.get(provider, 0)
    return ((input_tokens + output_tokens) / 1000) * rate