from google import genai
import httpx
import time
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def call_gemini(prompt: str) -> dict:
    start = time.time()
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    latency_ms = (time.time() - start) * 1000

    text = response.text
    input_tokens = len(prompt.split()) * 2
    output_tokens = len(text.split()) * 2

    return {
        "response": text,
        "latency_ms": round(latency_ms, 2),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "provider": "gemini",
        "model": "gemini-2.0-flash"
    }

def call_ollama(prompt: str) -> dict:
    start = time.time()
    try:
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json={"model": "gemma:2b", "prompt": prompt, "stream": False},
            timeout=60.0
        )
        latency_ms = (time.time() - start) * 1000
        data = response.json()
        text = data.get("response", "")
        input_tokens = len(prompt.split()) * 2
        output_tokens = len(text.split()) * 2

        return {
            "response": text,
            "latency_ms": round(latency_ms, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "provider": "ollama",
            "model": "gemma:2b"
        }
    except Exception as e:
        print(f"Ollama failed, falling back to Gemini: {e}")
        return call_gemini(prompt)

def call_llm(provider: str, prompt: str) -> dict:
    if provider == "gemini":
        return call_gemini(prompt)
    elif provider == "ollama":
        return call_ollama(prompt)
    else:
        return call_gemini(prompt)