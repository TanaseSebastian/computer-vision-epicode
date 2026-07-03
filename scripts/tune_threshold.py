import argparse
import csv
import json
from pathlib import Path

from app.vision import VerificationError, verify_identity
from evaluate import NEGATIVE_LABELS, POSITIVE_LABELS, confusion_counts, resolve_image_path, safe_divide


def collect_scores(csv_path: Path) -> list[dict]:
    rows = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for item in reader:
            image_value = item.get("image") or item.get("identity_image") or item.get("path")
            label = item.get("label", "").strip().lower()
            if not image_value or label not in POSITIVE_LABELS | NEGATIVE_LABELS:
                continue

            try:
                result = verify_identity(resolve_image_path(csv_path, image_value), threshold=0.5)
                score = result.score
                error = None
            except VerificationError as exc:
                score = 0.0
                error = str(exc)

            rows.append(
                {
                    "image": image_value,
                    "expected": label in POSITIVE_LABELS,
                    "score": score,
                    "error": error,
                }
            )
    return rows


def metrics_for_threshold(rows: list[dict], threshold: float) -> dict:
    classified = [
        {
            "expected": row["expected"],
            "predicted": row["score"] >= threshold,
        }
        for row in rows
    ]
    tp, tn, fp, fn = confusion_counts(classified)
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    f1 = safe_divide(2 * precision * recall, precision + recall)
    accuracy = safe_divide(tp + tn, len(rows))
    return {
        "threshold": round(threshold, 3),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
    }


def tune(csv_path: Path, start: float, stop: float, step: float) -> dict:
    rows = collect_scores(csv_path)
    thresholds = []
    current = start
    while current <= stop + 1e-9:
        thresholds.append(round(current, 3))
        current += step

    results = [metrics_for_threshold(rows, threshold) for threshold in thresholds]
    best = max(results, key=lambda item: (item["f1_score"], item["accuracy"], item["threshold"]))
    return {"samples": len(rows), "best": best, "thresholds": results, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description="Tune the identity-checker threshold on a labeled CSV.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--start", type=float, default=0.2)
    parser.add_argument("--stop", type=float, default=0.8)
    parser.add_argument("--step", type=float, default=0.02)
    parser.add_argument("--output", type=Path, default=Path("threshold_tuning.json"))
    args = parser.parse_args()

    report = tune(args.csv_path, args.start, args.stop, args.step)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"samples": report["samples"], "best": report["best"]}, indent=2))


if __name__ == "__main__":
    main()
