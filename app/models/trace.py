from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Trace(Base):
    __tablename__ = "traces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    provider = Column(String, nullable=False) 
    model = Column(String, nullable=False)
    latency_ms = Column(Float, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost_usd = Column(Float, nullable=False)
    complexity = Column(String, nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(String, nullable=False)
    relevance_score = Column(Float, nullable=False)   
    hallucination_score = Column(Float, nullable=False) 
    faithfulness_score = Column(Float, nullable=False) 
    overall_score = Column(Float, nullable=False) 
    judge_reasoning = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)