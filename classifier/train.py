import psycopg2
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
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
            t.input_tokens,
            t.output_tokens,
            t.latency_ms,
            t.complexity
        FROM traces t
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def train():
    print("Loading data from PostgreSQL...")
    df = load_data()
    print(f"Loaded {len(df)} samples")

    # label: complex (1) or simple (0)
    df["label"] = (df["complexity"] == "complex").astype(int)
    print(f"Complex: {df['label'].sum()}, Simple: {(df['label'] == 0).sum()}")

    df["text"] = df["prompt"] + " " + df["response"]

    X = df["text"]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced"))
    ])

    print("Training classifier...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    os.makedirs("classifier", exist_ok=True)
    with open("classifier/quality_classifier.pkl", "wb") as f:
        pickle.dump(pipeline, f)
    print("\nModel saved to classifier/quality_classifier.pkl")
    return accuracy

if __name__ == "__main__":
    train()