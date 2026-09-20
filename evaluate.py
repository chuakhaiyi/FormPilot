import json
import time
from pathlib import Path

from app.core import classify_document, extract_fields


def score(expected: str | None, actual: str | None) -> tuple[int, int, int]:
    expected = expected.strip().casefold() if expected else None
    actual = actual.strip().casefold() if actual else None
    return (int(bool(expected and actual and expected == actual)), int(bool(expected)), int(bool(actual)))


def main() -> None:
    rows = [json.loads(line) for line in Path("data/evaluation.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    tp = expected_count = actual_count = 0
    class_hits = 0
    started = time.perf_counter()
    for row in rows:
        prediction = extract_fields(row["text"])
        for field, expected in row["fields"].items():
            a, e, p = score(expected, prediction.get(field, {}).get("value"))
            tp += a; expected_count += e; actual_count += p
        class_hits += classify_document(row["text"])["type"] == row["document_type"]
    precision = tp / actual_count if actual_count else 0
    recall = tp / expected_count if expected_count else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    print(json.dumps({"field_precision": round(precision, 3), "field_recall": round(recall, 3), "field_f1": round(f1, 3), "classification_accuracy": round(class_hits / len(rows), 3), "avg_seconds": round((time.perf_counter() - started) / len(rows), 4)}, indent=2))


if __name__ == "__main__":
    main()
