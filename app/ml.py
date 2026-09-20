from __future__ import annotations

import json
from pathlib import Path


def train_classifier(dataset: str = "data/evaluation.jsonl", output: str = "models/document_classifier.joblib") -> None:
    from joblib import dump
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    rows = [json.loads(line) for line in Path(dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
        ("classifier", LogisticRegression(max_iter=500)),
    ])
    model.fit([row["text"] for row in rows], [row["document_type"] for row in rows])
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    dump(model, target)


if __name__ == "__main__":
    train_classifier()
