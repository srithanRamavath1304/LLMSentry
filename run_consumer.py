import threading
from app.kafka.consumers import run_trace_consumer, run_evaluation_consumer

if __name__ == "__main__":
    t1 = threading.Thread(target=run_trace_consumer, daemon=True)
    t2 = threading.Thread(target=run_evaluation_consumer, daemon=True)

    t1.start()
    t2.start()

    print("Both consumers running...")
    t1.join()
    t2.join()