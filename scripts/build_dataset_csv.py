import argparse
import csv
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
POSITIVE_DIR_NAMES = {"match", "same", "positive", "positives"}
NEGATIVE_DIR_NAMES = {"no_match", "different", "negative", "negatives"}


def infer_label(path: Path) -> str | None:
    parts = {part.lower() for part in path.parts}
    if parts & POSITIVE_DIR_NAMES:
        return "match"
    if parts & NEGATIVE_DIR_NAMES:
        return "no_match"

    name = path.stem.lower()
    if any(token in name for token in ("no_match", "different", "negative")):
        return "no_match"
    if any(token in name for token in ("match", "same", "positive")):
        return "match"
    return None


def build_rows(dataset_dir: Path) -> list[dict[str, str]]:
    rows = []
    for path in sorted(dataset_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        label = infer_label(path.relative_to(dataset_dir))
        if label is None:
            continue

        rows.append({"image": str(path), "label": label})
    return rows


def main():
    parser = argparse.ArgumentParser(description="Build samples.csv from a labeled image folder.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("samples.csv"))
    args = parser.parse_args()

    rows = build_rows(args.dataset_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image", "label"])
        writer.writeheader()
        writer.writerows(rows)

    positives = sum(1 for row in rows if row["label"] == "match")
    negatives = sum(1 for row in rows if row["label"] == "no_match")
    print(f"Wrote {len(rows)} rows to {args.output}")
    print(f"Positive: {positives}")
    print(f"Negative: {negatives}")
    if not rows:
        print("No rows found. Use folders named match/ and no_match/, or filenames containing match/no_match.")


if __name__ == "__main__":
    main()
