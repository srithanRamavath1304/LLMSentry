from fastapi import APIRouter
from sqlalchemy import func
from app.models.database import SessionLocal
from app.models.trace import Trace, Evaluation
from fastapi.responses import HTMLResponse

router = APIRouter()

def get_stats():
    db = SessionLocal()
    try:
        total_traces = db.query(func.count(Trace.id)).scalar()
        avg_latency = db.query(func.avg(Trace.latency_ms)).scalar() or 0
        total_cost = db.query(func.sum(Trace.cost_usd)).scalar() or 0
        
        provider_counts = db.query(
            Trace.provider, func.count(Trace.id)
        ).group_by(Trace.provider).all()
        
        complexity_counts = db.query(
            Trace.complexity, func.count(Trace.id)
        ).group_by(Trace.complexity).all()
        
        avg_scores = db.query(
            func.avg(Evaluation.relevance_score),
            func.avg(Evaluation.hallucination_score),
            func.avg(Evaluation.overall_score)
        ).first()

        recent_traces = db.query(Trace).order_by(
            Trace.created_at.desc()
        ).limit(10).all()

        return {
            "total_traces": total_traces,
            "avg_latency": round(avg_latency, 2),
            "total_cost": round(total_cost, 6),
            "provider_counts": dict(provider_counts),
            "complexity_counts": dict(complexity_counts),
            "avg_relevance": round(avg_scores[0] or 0, 3),
            "avg_hallucination": round(avg_scores[1] or 0, 3),
            "avg_overall": round(avg_scores[2] or 0, 3),
            "recent_traces": [
                {
                    "id": t.id[:8],
                    "prompt": t.prompt[:50],
                    "provider": t.provider,
                    "complexity": t.complexity,
                    "latency_ms": t.latency_ms,
                    "cost_usd": t.cost_usd,
                } for t in recent_traces
            ]
        }
    finally:
        db.close()

@router.get("/stats")
def stats():
    return get_stats()

@router.get("/", response_class=HTMLResponse)
def dashboard():
    s = get_stats()
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>LLMSentry Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ font-family: Arial, sans-serif; background: #0f0f0f; color: #fff; padding: 20px; }}
        h1 {{ color: #00ff88; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
        .card {{ background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 20px; }}
        .card h3 {{ color: #888; font-size: 12px; margin: 0 0 8px 0; text-transform: uppercase; }}
        .card .value {{ font-size: 28px; font-weight: bold; color: #00ff88; }}
        table {{ width: 100%; border-collapse: collapse; background: #1a1a1a; border-radius: 8px; overflow: hidden; }}
        th {{ background: #222; padding: 12px; text-align: left; color: #888; font-size: 12px; text-transform: uppercase; }}
        td {{ padding: 12px; border-top: 1px solid #222; font-size: 14px; }}
        .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
        .ollama {{ background: #1a3a2a; color: #00ff88; }}
        .gemini {{ background: #1a2a3a; color: #00aaff; }}
        .simple {{ background: #2a2a1a; color: #ffaa00; }}
        .complex {{ background: #2a1a1a; color: #ff4444; }}
        h2 {{ color: #888; margin-top: 30px; }}
    </style>
</head>
<body>
    <h1>⚡ LLMSentry</h1>
    <p style="color:#555">Real-time LLM Observability Platform — refreshes every 10s</p>
    
    <div class="grid">
        <div class="card">
            <h3>Total Traces</h3>
            <div class="value">{s['total_traces']}</div>
        </div>
        <div class="card">
            <h3>Avg Latency</h3>
            <div class="value">{s['avg_latency']}ms</div>
        </div>
        <div class="card">
            <h3>Total Cost</h3>
            <div class="value">${s['total_cost']}</div>
        </div>
        <div class="card">
            <h3>Avg Quality Score</h3>
            <div class="value">{s['avg_overall']}</div>
        </div>
    </div>

    <div class="grid" style="grid-template-columns: repeat(3, 1fr)">
        <div class="card">
            <h3>Avg Relevance</h3>
            <div class="value">{s['avg_relevance']}</div>
        </div>
        <div class="card">
            <h3>Avg Hallucination</h3>
            <div class="value">{s['avg_hallucination']}</div>
        </div>
        <div class="card">
            <h3>Providers</h3>
            <div class="value">{s['provider_counts']}</div>
        </div>
    </div>

    <h2>Recent Traces</h2>
    <table>
        <tr>
            <th>ID</th><th>Prompt</th><th>Provider</th>
            <th>Complexity</th><th>Latency</th><th>Cost</th>
        </tr>
        {"".join(f'''<tr>
            <td>{t['id']}</td>
            <td>{t['prompt']}</td>
            <td><span class="badge {t['provider']}">{t['provider']}</span></td>
            <td><span class="badge {t['complexity']}">{t['complexity']}</span></td>
            <td>{t['latency_ms']}ms</td>
            <td>${t['cost_usd']}</td>
        </tr>''' for t in s['recent_traces'])}
    </table>
</body>
</html>
"""
    return html