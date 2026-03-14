import psycopg2
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
import pickle
import os
from dotenv import load_dotenv

load_dotenv()

def load_data():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    query = """
        SELECT 
            t.prompt,
            t.response,
            e.relevance_score,
            e.hallucination_score,
            e.faithfulness_score,
            e.overall_score
        FROM traces t
        JOIN evaluations e ON t.id = e.trace_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def train():
    print("Loading data from PostgreSQL...")
    df = load_data()
    print(f"Loaded {len(df)} samples")

    df["text"] = df["prompt"] + " " + df["response"]
    X = df["text"]

    results = {}

    for target in ["overall_score", "relevance_score", "hallucination_score", "faithfulness_score"]:
        print(f"\nTraining {target} model...")
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
            ("reg", RandomForestRegressor(n_estimators=100, random_state=42))
        ])

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        print(f"R2 Score: {r2:.3f}, MSE: {mse:.4f}")
        results[target] = {"r2": r2, "mse": mse, "model": pipeline}

    os.makedirs("classifier", exist_ok=True)
    with open("classifier/evaluator_model.pkl", "wb") as f:
        pickle.dump({k: v["model"] for k, v in results.items()}, f)
    print("\nEvaluator model saved to classifier/evaluator_model.pkl")

    return results

if __name__ == "__main__":
    train()