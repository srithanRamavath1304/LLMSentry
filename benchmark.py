# benchmark.py
import time
import httpx
import pickle
import os
from dotenv import load_dotenv

load_dotenv()

clf = pickle.load(open("classifier/quality_classifier.pkl", "rb"))
evaluator = pickle.load(open("classifier/evaluator_model.pkl", "rb"))

TEST_CASES = [
    # simple
    ("What is the capital of France?", "The capital of France is Paris."),
    ("Who invented the telephone?", "Alexander Graham Bell invented the telephone."),
    ("What is 15 multiplied by 7?", "15 multiplied by 7 is 105."),
    ("What is the capital of Japan?", "The capital of Japan is Tokyo."),
    ("What is SQL?", "SQL is a language for managing relational databases."),
    # complex
    ("Explain how transformers work in detail", "Transformers use self-attention mechanisms to process sequences in parallel, enabling long range dependency capture."),
    ("Describe the differences between LSTM and GRU architectures", "LSTMs have three gates while GRUs have two, making GRUs simpler and faster to train."),
    ("How does backpropagation work in neural networks?", "Backpropagation computes gradients using the chain rule and updates weights to minimize loss."),
    ("Explain the CAP theorem and its implications", "CAP theorem states distributed systems can only guarantee two of consistency, availability, and partition tolerance."),
    ("Compare supervised and unsupervised learning with examples", "Supervised learning uses labeled data like image classification, unsupervised finds patterns like clustering."),
]

runs = len(TEST_CASES)

def avg(times):
    return round(sum(times) / len(times), 2)

# sklearn classification
times = []
for prompt, _ in TEST_CASES:
    start = time.time()
    clf.predict([prompt])
    times.append((time.time() - start) * 1000)
print(f"Sklearn classification avg: {avg(times)}ms")

# sklearn evaluation
times = []
for prompt, response in TEST_CASES:
    start = time.time()
    text = prompt + " " + response
    {metric: float(model.predict([text])[0]) for metric, model in evaluator.items()}
    times.append((time.time() - start) * 1000)
print(f"Sklearn evaluation avg: {avg(times)}ms")

# ollama classification
times = []
for prompt, _ in TEST_CASES:
    start = time.time()
    httpx.post("http://localhost:11434/api/generate",
        json={"model": "gemma:2b", "prompt": f"classify as simple or complex, reply one word: {prompt}", "stream": False},
        timeout=60.0)
    times.append((time.time() - start) * 1000)
print(f"Ollama classification avg: {avg(times)}ms")

# ollama evaluation
times = []
for prompt, response in TEST_CASES:
    start = time.time()
    httpx.post("http://localhost:11434/api/generate",
        json={"model": "gemma:2b", "prompt": f"score relevance, hallucination, faithfulness of this response: {response}", "stream": False},
        timeout=60.0)
    times.append((time.time() - start) * 1000)
print(f"Ollama evaluation avg: {avg(times)}ms")

# gemini evaluation
from google import genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
times = []
for prompt, response in TEST_CASES:
    start = time.time()
    client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"score relevance, hallucination, faithfulness of this response to the question: {prompt}\nResponse: {response}")
    times.append((time.time() - start) * 1000)
print(f"Gemini evaluation avg: {avg(times)}ms")