import argparse
import csv
from pathlib import Path


VALID_LABELS = {"1", "true", "match", "same", "positive", "yes", "0", "false", "no_match", "different", "negative", "no"}


def resolve_image_path(csv_path: Path, image_value: str) -> Path:
    image_path = Path(image_value)
    if image_path.is_absolute():
        return image_path

    relative_to_csv = csv_path.parent / image_path
    if relative_to_csv.exists():
        return relative_to_csv

    return image_path


def validate(csv_path: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {"rows": 0, "positive": 0, "negative": 0, "missing_files": 0}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return ["CSV vuoto o senza header."], counts

        if "label" not in reader.fieldnames:
            errors.append("Manca la colonna obbligatoria 'label'.")

        image_column = next((name for name in ("image", "identity_image", "path") if name in reader.fieldnames), None)
        if image_column is None:
            errors.append("Manca una colonna immagine: usa 'image', 'identity_image' o 'path'.")
            return errors, counts

        for index, row in enumerate(reader, start=2):
            counts["rows"] += 1
            image_path = resolve_image_path(csv_path, row.get(image_column, ""))
            label = row.get("label", "").strip().lower()

            if not image_path.exists():
                counts["missing_files"] += 1
                errors.append(f"Riga {index}: file non trovato: {image_path}")

            if label not in VALID_LABELS:
                errors.append(f"Riga {index}: label non valida: {row.get('label')!r}")
            elif label in {"1", "true", "match", "same", "positive", "yes"}:
                counts["positive"] += 1
            else:
                counts["negative"] += 1

    if counts["rows"] == 0:
        errors.append("Il CSV non contiene righe dati.")

    if counts["positive"] == 0 or counts["negative"] == 0:
        errors.append("Warning: il dataset non contiene entrambe le classi; le metriche saranno incomplete.")

    return errors, counts


def main():
    parser = argparse.ArgumentParser(description="Validate an identity-checker dataset CSV.")
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    errors, counts = validate(args.csv_path)
    print(f"Rows: {counts['rows']}")
    print(f"Positive: {counts['positive']}")
    print(f"Negative: {counts['negative']}")
    print(f"Missing files: {counts['missing_files']}")
    if errors:
        print("\nIssues:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1 if counts["missing_files"] else 0)

    print("\nDataset CSV valido.")


if __name__ == "__main__":
    main()
