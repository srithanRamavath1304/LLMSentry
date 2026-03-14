import httpx
import time
import random

PROMPTS = [
    # simple - factual
    "What is the capital of France?",
    "Who is the CEO of Tesla?",
    "What is 15 multiplied by 7?",
    "Define machine learning",
    "What is the capital of Japan?",
    "How many planets are in the solar system?",
    "What is the boiling point of water?",
    "Who invented the telephone?",
    "What is the speed of light?",
    "Define neural network",
    "What is the capital of Germany?",
    "Who founded Microsoft?",
    "What is 256 divided by 16?",
    "What is the capital of Australia?",
    "Who wrote Harry Potter?",
    "What is the atomic number of carbon?",
    "What is RAM in computers?",
    "Who invented the internet?",
    "What is the capital of Brazil?",
    "What is Python programming language?",
    "Who is the founder of Amazon?",
    "What is the largest planet in the solar system?",
    "What is SQL?",
    "What is the capital of Canada?",
    "Who invented the light bulb?",
    "What is an API?",
    "What is the capital of India?",
    "What is machine learning?",
    "Who founded Google?",
    "What is the speed of sound?",
    "What is the capital of China?",
    "Define deep learning",
    "What is Docker?",
    "Who invented electricity?",
    "What is the capital of Russia?",
    "What is Kafka?",
    "Who founded Apple?",
    "What is Redis?",
    "What is the capital of Italy?",
    "What is PostgreSQL?",
    # complex - explanations
    "Explain the architectural differences between transformer and RNN based language models briefly",
    "Describe how attention mechanisms work in deep learning",
    "Compare supervised and unsupervised learning with examples",
    "Explain how Kafka achieves fault tolerance in distributed systems",
    "Analyze the tradeoffs between SQL and NoSQL databases",
    "Explain how Redis handles cache eviction policies",
    "Describe the CAP theorem and its implications",
    "How does backpropagation work in neural networks?",
    "Explain the difference between L1 and L2 regularization",
    "Discuss the ethical implications of large language models",
    "Explain how BERT differs from GPT in architecture and use cases",
    "Describe the working of a convolutional neural network in detail",
    "How does the transformer positional encoding work?",
    "Explain the concept of transfer learning in deep learning",
    "Compare microservices and monolithic architecture with tradeoffs",
    "How does consistent hashing work in distributed systems?",
    "Explain the differences between TCP and UDP protocols",
    "Describe how garbage collection works in Java",
    "How does a load balancer work in a distributed system?",
    "Explain the SOLID principles in software engineering",
    "Describe how vector databases work and their use cases",
    "How does RAG (Retrieval Augmented Generation) work?",
    "Explain the concept of embeddings in NLP",
    "Describe the differences between LSTM and GRU architectures",
    "How does the Adam optimizer work in deep learning?",
    "Explain how distributed transactions work with two-phase commit",
    "Describe the working of a recommendation system",
    "How does Docker containerization differ from virtual machines?",
    "Explain the concept of attention in transformers with an example",
    "Describe how Kubernetes manages container orchestration",
    "How does gradient descent optimization work?",
    "Explain the differences between batch and stream processing",
    "Describe how a content delivery network (CDN) works",
    "How does OAuth 2.0 authentication work?",
    "Explain the concept of zero-shot learning in AI",
    "Describe the working of a graph neural network",
    "How does database indexing improve query performance?",
    "Explain the differences between supervised fine-tuning and RLHF",
    "Describe how MapReduce works in big data processing",
    "How does the PageRank algorithm work?",
    "Explain the concept of model quantization in deep learning",
    "Describe how event sourcing works in distributed systems",
    "How does a variational autoencoder work?",
    "Explain the differences between precision and recall in ML",
    "Describe how knowledge distillation works in machine learning",
    "How does HTTPS encryption work?",
    "Explain the working of a generative adversarial network",
    "Describe how prompt engineering affects LLM outputs",
    "How does federated learning work?",
    "Explain the concept of hallucination in large language models",
    "Describe the differences between fine-tuning and prompt engineering",
    "How does a message queue differ from a database?",
    "Explain the working of the RAFT consensus algorithm",
    "Describe how neural architecture search works",
    "How does semantic search differ from keyword search?",
    "Explain the concept of chain of thought prompting",
    "Describe how LLM inference optimization works with quantization",
    "How does the mixture of experts architecture work in LLMs?",
    "Explain the concept of context window in language models",
    "Describe how reinforcement learning from human feedback works",
    "How does multi-head attention improve transformer performance?",
]

def send_prompt(prompt: str):
    try:
        response = httpx.post(
            "http://127.0.0.1:8000/api/v1/chat",
            json={"prompt": prompt},
            timeout=120.0
        )
        data = response.json()
        print(f"✓ [{data['complexity']}] [{data['provider']}] {prompt[:40]}... ({data['latency_ms']}ms)")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    total = 0
    print("Starting simulator... Target: 128 requests")
    while total < 128:
        prompt = random.choice(PROMPTS)
        send_prompt(prompt)
        total += 1
        print(f"Progress: {total}/128")
        time.sleep(1)
    print("Done! 128 traces generated.")

    #128 remaining