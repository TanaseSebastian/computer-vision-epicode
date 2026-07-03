import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.vision import VerificationError, verify_identity


POSITIVE_LABELS = {"1", "true", "match", "same", "positive", "yes"}
NEGATIVE_LABELS = {"0", "false", "no_match", "different", "negative", "no"}


def resolve_image_path(csv_path: Path, image_value: str) -> Path:
    image_path = Path(image_value)
    if image_path.is_absolute():
        return image_path

    relative_to_csv = csv_path.parent / image_path
    if relative_to_csv.exists():
        return relative_to_csv

    return image_path


def confusion_counts(rows):
    tp = sum(1 for row in rows if row["expected"] and row["predicted"])
    tn = sum(1 for row in rows if not row["expected"] and not row["predicted"])
    fp = sum(1 for row in rows if not row["expected"] and row["predicted"])
    fn = sum(1 for row in rows if row["expected"] and not row["predicted"])
    return tp, tn, fp, fn


def safe_divide(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def evaluate(csv_path: Path, threshold: float):
    rows = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "label" not in reader.fieldnames:
            raise ValueError("Il CSV deve contenere una colonna 'label'.")

        for item in reader:
            image_value = item.get("image") or item.get("identity_image") or item.get("path")
            if not image_value:
                raise ValueError("Il CSV deve contenere una colonna 'image', 'identity_image' o 'path'.")

            label = item["label"].strip().lower()
            if label not in POSITIVE_LABELS | NEGATIVE_LABELS:
                raise ValueError(f"Label non riconosciuta: {item['label']!r}")

            expected = label in POSITIVE_LABELS
            image_path = resolve_image_path(csv_path, image_value)
            try:
                result = verify_identity(image_path, threshold=threshold)
                rows.append(
                    {
                        "image": str(image_path),
                        "expected": expected,
                        "predicted": result.match,
                        "score": result.score,
                        "method": result.method,
                        "error": None,
                    }
                )
            except VerificationError as exc:
                rows.append(
                    {
                        "image": str(image_path),
                        "expected": expected,
                        "predicted": False,
                        "score": 0.0,
                        "method": "error",
                        "error": str(exc),
                    }
                )

    tp, tn, fp, fn = confusion_counts(rows)
    total = len(rows)
    positives = sum(1 for row in rows if row["expected"])
    negatives = total - positives
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    f1 = safe_divide(2 * precision * recall, precision + recall)

    return {
        "threshold": threshold,
        "samples": total,
        "positive_samples": positives,
        "negative_samples": negatives,
        "accuracy": round(safe_divide(tp + tn, total), 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": {
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
        },
        "rows": rows,
    }


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def build_markdown_report(report: dict) -> str:
    matrix = report["confusion_matrix"]
    lines = [
        "# Evaluation Report",
        "",
        f"- Threshold: `{report['threshold']}`",
        f"- Samples: `{report['samples']}`",
        f"- Positive samples: `{report['positive_samples']}`",
        f"- Negative samples: `{report['negative_samples']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Accuracy | {format_percent(report['accuracy'])} |",
        f"| Precision | {format_percent(report['precision'])} |",
        f"| Recall | {format_percent(report['recall'])} |",
        f"| F1-score | {format_percent(report['f1_score'])} |",
        "",
        "## Confusion Matrix",
        "",
        "|  | Predicted match | Predicted no match |",
        "| --- | ---: | ---: |",
        f"| Actual match | {matrix['true_positive']} | {matrix['false_negative']} |",
        f"| Actual no match | {matrix['false_positive']} | {matrix['true_negative']} |",
        "",
    ]

    if report["positive_samples"] == 0 or report["negative_samples"] == 0:
        lines.extend(
            [
                "## Dataset Warning",
                "",
                "The dataset is not balanced across both classes. Full precision/F1/false-positive analysis requires both positive and negative samples.",
                "",
            ]
        )

    error_rows = [row for row in report["rows"] if row["error"]]
    if error_rows:
        lines.extend(["## Processing Errors", "", "| Image | Error |", "| --- | --- |"])
        for row in error_rows:
            lines.append(f"| `{row['image']}` | {row['error']} |")
        lines.append("")

    return "\n".join(lines)


def update_technical_analysis(technical_path: Path, report: dict) -> None:
    text = technical_path.read_text(encoding="utf-8")
    report_md = build_markdown_report(report)
    start = text.index("## 6. Results")
    end = text.index("## 7. Failure Analysis")
    replacement = "## 6. Results\n\n" + report_md.split("\n", 2)[2].strip() + "\n\n"
    technical_path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def load_font(size: int):
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def save_confusion_matrix_plot(report: dict, output: Path) -> None:
    matrix = report["confusion_matrix"]
    values = [
        [matrix["true_positive"], matrix["false_negative"]],
        [matrix["false_positive"], matrix["true_negative"]],
    ]
    labels = [["TP", "FN"], ["FP", "TN"]]
    max_value = max(max(row) for row in values) or 1

    image = Image.new("RGB", (760, 620), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(34)
    text_font = load_font(24)
    number_font = load_font(42)

    draw.text((40, 30), "Confusion Matrix", fill=(29, 37, 35), font=title_font)
    draw.text((250, 95), "Predicted match", fill=(96, 113, 109), font=text_font)
    draw.text((470, 95), "Predicted no match", fill=(96, 113, 109), font=text_font)
    draw.text((35, 205), "Actual match", fill=(96, 113, 109), font=text_font)
    draw.text((35, 425), "Actual no match", fill=(96, 113, 109), font=text_font)

    colors = ((18, 106, 90), (217, 93, 57))
    for row in range(2):
        for col in range(2):
            x = 250 + col * 220
            y = 160 + row * 220
            value = values[row][col]
            intensity = int(245 - (value / max_value) * 105)
            base = colors[0] if row == col else colors[1]
            fill = tuple(int((channel + intensity) / 2) for channel in base)
            draw.rectangle((x, y, x + 180, y + 180), fill=fill, outline=(215, 225, 222), width=2)
            draw.text((x + 20, y + 24), labels[row][col], fill="white", font=text_font)
            draw.text((x + 70, y + 82), str(value), fill="white", font=number_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def save_score_plot(report: dict, output: Path) -> None:
    rows = report["rows"]
    image = Image.new("RGB", (900, 520), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(34)
    text_font = load_font(22)

    draw.text((40, 30), "Similarity Scores by Class", fill=(29, 37, 35), font=title_font)
    left, top, right, bottom = 90, 110, 840, 430
    draw.rectangle((left, top, right, bottom), outline=(215, 225, 222), width=2)

    for tick in range(0, 11):
        x = left + int((right - left) * tick / 10)
        draw.line((x, bottom, x, bottom + 8), fill=(96, 113, 109), width=1)
        draw.text((x - 10, bottom + 15), f"{tick / 10:.1f}", fill=(96, 113, 109), font=text_font)

    draw.text((left, bottom + 58), "Score", fill=(96, 113, 109), font=text_font)
    draw.text((left, top - 35), "match", fill=(18, 106, 90), font=text_font)
    draw.text((left, top + 120), "no_match", fill=(217, 93, 57), font=text_font)

    for index, row in enumerate(rows):
        x = left + int((right - left) * max(0.0, min(1.0, row["score"])))
        y_base = top + 40 if row["expected"] else top + 190
        y = y_base + (index % 5) * 18
        color = (18, 106, 90) if row["expected"] else (217, 93, 57)
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def save_plots(report: dict, output_dir: Path) -> None:
    save_confusion_matrix_plot(report, output_dir / "confusion_matrix.png")
    save_score_plot(report, output_dir / "score_distribution.png")


def main():
    parser = argparse.ArgumentParser(description="Evaluate the single-image identity checker.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--threshold", type=float, default=0.363)
    parser.add_argument("--output", type=Path, default=Path("evaluation_results.json"))
    parser.add_argument("--report", type=Path, default=Path("docs/evaluation_report.md"))
    parser.add_argument("--plots-dir", type=Path, default=Path("docs/figures"))
    parser.add_argument(
        "--update-technical-analysis",
        action="store_true",
        help="Replace the Results section in docs/technical_analysis.md with the current metrics.",
    )
    args = parser.parse_args()

    report = evaluate(args.csv_path, args.threshold)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.report.write_text(build_markdown_report(report), encoding="utf-8")
    save_plots(report, args.plots_dir)
    if args.update_technical_analysis:
        update_technical_analysis(Path("docs/technical_analysis.md"), report)

    print(json.dumps({key: report[key] for key in report if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
