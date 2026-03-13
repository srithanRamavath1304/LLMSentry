from kafka import KafkaProducer
import json
import os
from dotenv import load_dotenv

load_dotenv()

producer = None

def get_producer():
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=3
        )
    return producer

def publish_trace(trace: dict):
    get_producer().send("llm.traces", value=trace)

def publish_evaluation_request(trace: dict):
    get_producer().send("llm.evaluations", value=trace)