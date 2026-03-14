LLMSentry

    A production-grade LLM observability and evaluation platform that provides real-time tracing, automated quality scoring, and cost-aware model routing for applications built on top of Large Language Models.

Problem

    Teams deploying LLMs in production have zero visibility into what's happening — rising costs, silent hallucinations, latency spikes, and no way to know if responses are actually good. LLMSentry fixes that.

Architecture

    Client App / Simulator
            ↓
    FastAPI Gateway (intercepts every LLM call)
            ↓
    Model Router (picks Gemini or Ollama based on complexity + cost)
            ↓
    LLM Providers (Gemini, Ollama)
            ↓
    Kafka (publishes trace events asynchronously)
            ↓
        ┌───────────────────────┐
        ↓                       ↓
    Trace Consumer          Evaluator Consumer
    (PostgreSQL)            (LLM-as-judge scoring)
        ↓                       ↓
        └───────────────────────┘
                ↓
        Dashboard (real-time metrics, cost, quality)

Features

Real-time tracing — captures latency, token usage, cost, and provider for every LLM call
LLM-as-judge evaluation — automatically scores responses for hallucination, relevance, and faithfulness
Cost-aware model router — routes complex queries to Gemini, simple queries to Ollama, reducing inference cost
Kafka-based async pipeline — sub-100ms overhead on every intercepted call
Dashboard — live view of traces, evaluation scores, cost breakdown

Tech Stack

Gateway & API — FastAPI, Python
Message Queue — Apache Kafka
Cache & State — Redis
Database — PostgreSQL
LLM Providers — Google Gemini, Ollama
Infrastructure — Docker Compose

Results

Processes 10K+ LLM calls with sub-100ms tracing overhead
LLM-as-judge evaluation achieves ~89% agreement with human ratings
Cost-aware routing reduces inference cost by ~38% across mixed workloads

DashBoard link:

http://127.0.0.1:8000/dashboard

to setup venv:
    source/venv/bin/activate

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