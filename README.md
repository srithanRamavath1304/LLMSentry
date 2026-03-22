# LLMSentry

A production-grade LLM observability and evaluation platform that provides real-time tracing, automated quality scoring, and cost-aware model routing for applications built on top of Large Language Models.

## Problem

Teams deploying LLMs in production have zero visibility into what's happening — rising costs, silent hallucinations, latency spikes, and no way to know if responses are actually good. LLMSentry fixes that.

## Architecture
```
Client App / Simulator
        ↓
FastAPI Gateway (intercepts every LLM call)
        ↓
Model Router (LLM-based complexity classifier → Gemini or Ollama)
        ↓
LLM Providers (Gemini 2.5 Flash Lite, Ollama Gemma-2B)
        ↓
Kafka (publishes trace events asynchronously)
        ↓
    ┌───────────────────────┐
    ↓                       ↓
Trace Consumer          Evaluator Consumer
(PostgreSQL)            (Gemini / Sklearn)
    ↓                       ↓
    └───────────────────────┘
            ↓
      Dashboard (real-time metrics, cost, quality)
```

## Features

- **Real-time tracing** — captures latency, token usage, cost, and provider for every LLM call with sub-100ms overhead
- **LLM-as-judge evaluation** — automatically scores responses for hallucination, relevance, and faithfulness using Gemini as judge
- **Cost-aware model router** — routes ~60% of queries to zero-cost local Ollama, complex queries to Gemini
- **Sklearn distilled classifier** — complexity classifier trained via knowledge distillation, 93x faster than LLM-based classification (5.67ms vs 528ms)
- **Sklearn distilled evaluator** — evaluation model trained on Gemini judge labels, 60x+ faster than Gemini inference (29ms vs 2347ms)
- **Configurable via env** — switch between sklearn/ollama/gemini for both classification and evaluation
- **Live dashboard** — real-time metrics, cost breakdown, evaluation scores, recent traces

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Gateway & API | FastAPI, Python |
| Message Queue | Apache Kafka |
| Cache & Routing | Redis |
| Database | PostgreSQL |
| LLM Providers | Google Gemini 2.5 Flash Lite, Ollama (Gemma-2B) |
| ML Models | Scikit-learn, TF-IDF, Random Forest |
| Infrastructure | Docker Compose |

## Getting Started
```bash
git clone https://github.com/srithanRamavath1304/LLMSentry
cd LLMSentry
cp .env.example .env
# Add your Gemini API key to .env
docker-compose up -d
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In a separate terminal:
```bash
python run_consumers.py
```

## Environment Variables
```env
GEMINI_API_KEY=your_key_here
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/llmsentry
COMPLEXITY_CLASSIFIER=sklearn   # or "ollama"
EVALUATOR_TYPE=sklearn          # or "ollama" or "gemini"
```

## Project Structure
```
llmsentry/
├── app/
│   ├── gateway/        # FastAPI routes, LLM caller
│   ├── router/         # Cost-aware model router, complexity classifier
│   ├── kafka/          # Producer, trace and evaluation consumers
│   ├── evaluator/      # LLM-as-judge scoring
│   ├── models/         # DB models, database connection
│   └── dashboard/      # Real-time metrics UI
├── classifier/         # Sklearn training scripts and saved models
├── simulator/          # Traffic simulation for load testing
├── run_consumers.py    # Starts both Kafka consumers in parallel
├── docker-compose.yml
└── .env.example
```

## Benchmarks

| Method | Classification Latency | Evaluation Latency |
|--------|----------------------|-------------------|
| Sklearn | 5.67ms | 29.58ms |
| Ollama | 528ms | 2347ms |
| Gemini | — | 1874ms |

Sklearn complexity classifier achieves **89.8% accuracy** on test set.

## Key Design Decisions

**Why Kafka?**
Trace saving and evaluation are decoupled from the request path. Publishing to Kafka adds <10ms overhead vs 50-100ms for synchronous DB writes.

**Why two separate Kafka topics?**
Trace saving (fast) and evaluation (slow) are independent operations. Separating them means slow evaluation never blocks trace persistence.

**Why Redis for routing cache?**
Routing decisions are deterministic for the same prompt. Caching avoids re-running the classifier for repeated queries — critical at scale.

**Why knowledge distillation?**
LLM-based classification (528ms) and evaluation (1078ms) are too slow for production. Training sklearn models on LLM-generated labels gives comparable quality at 30x lower latency.

**Why switch from Gemma-2B to Gemini for evaluation labels?**
Gemma-2B showed severe score anchoring bias — 75% of evaluations returned exactly 0.88, giving near-zero variance. Gemini produced scores across the full 0-1 range (StdDev 0.28), enabling meaningful distillation.

DashBoard link:

http://127.0.0.1:8000/dashboard

to setup venv:
    source venv/bin/activate

to run ollama locally:
    first check if its already running: pkill ollama
    then: ollama serve

to run application:
    uvicorn app.main:app --reload  

to run consumer: 
    python run_consumer.py  

to hit api:
    curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'