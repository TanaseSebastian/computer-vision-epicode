import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "app/__init__.py",
    "app/__main__.py",
    "app/routes.py",
    "app/vision.py",
    "app/templates/index.html",
    "app/static/styles.css",
    "evaluate.py",
    "requirements.txt",
    "README.md",
    "Dockerfile",
    ".dockerignore",
    "openapi.json",
    "docs/architecture.md",
    "docs/api.md",
    "docs/technical_analysis.md",
    "docs/technical_analysis.pdf",
    "docs/requirements_coverage.md",
    "docs/evaluation_dataset.md",
    "docs/deployment.md",
    "docs/privacy_and_ethics.md",
    "docs/model_card.md",
    "docs/references.md",
    "docs/oral_presentation_outline.md",
    "docs/submission_checklist.md",
    ".github/workflows/tests.yml",
    "samples.csv",
    "scripts/build_dataset_csv.py",
    "scripts/download_models.py",
    "scripts/validate_dataset.py",
    "scripts/tune_threshold.py",
    "scripts/finalize_submission.py",
    "scripts/package_submission.py",
    "scripts/export_technical_pdf.py",
    "scripts/windows/setup.ps1",
    "scripts/windows/check.ps1",
    "scripts/windows/evaluate_dataset.ps1",
    "tests/test_app.py",
]


def status(ok: bool) -> str:
    return "OK" if ok else "MISSING"


def check_files() -> list[dict]:
    return [
        {"check": f"file:{path}", "ok": (ROOT / path).exists()}
        for path in REQUIRED_FILES
    ]


def check_models() -> list[dict]:
    return [
        {
            "check": "model:face_detection_yunet_2023mar.onnx",
            "ok": (ROOT / "models" / "face_detection_yunet_2023mar.onnx").exists(),
        },
        {
            "check": "model:face_recognition_sface_2021dec.onnx",
            "ok": (ROOT / "models" / "face_recognition_sface_2021dec.onnx").exists(),
        },
    ]


def check_samples(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return [{"check": "dataset:samples.csv exists", "ok": False}]

    rows = 0
    existing_files = 0
    positives = 0
    negatives = 0
    positive_labels = {"1", "true", "match", "same", "positive", "yes"}
    negative_labels = {"0", "false", "no_match", "different", "negative", "no"}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            image_value = row.get("image") or row.get("identity_image") or row.get("path") or ""
            image_path = Path(image_value)
            relative_to_csv = csv_path.parent / image_path
            if image_path.exists() or relative_to_csv.exists() or (ROOT / image_value).exists():
                existing_files += 1

            label = row.get("label", "").strip().lower()
            if label in positive_labels:
                positives += 1
            elif label in negative_labels:
                negatives += 1

    return [
        {"check": "dataset:has rows", "ok": rows > 0, "details": rows},
        {"check": "dataset:all image files exist", "ok": rows > 0 and existing_files == rows, "details": f"{existing_files}/{rows}"},
        {"check": "dataset:has positive samples", "ok": positives > 0, "details": positives},
        {"check": "dataset:has negative samples", "ok": negatives > 0, "details": negatives},
    ]


def run_pytest() -> dict:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "check": "tests:pytest",
        "ok": result.returncode == 0,
        "details": (result.stdout + result.stderr).strip().splitlines()[-1] if (result.stdout + result.stderr).strip() else "",
    }


def main():
    checks = []
    checks.extend(check_files())
    checks.extend(check_models())
    checks.extend(check_samples(ROOT / "samples.csv"))
    checks.append(run_pytest())

    report = {"checks": checks, "passed": sum(1 for item in checks if item["ok"]), "total": len(checks)}
    print(json.dumps(report, indent=2))

    hard_failures = [
        item
        for item in checks
        if not item["ok"] and not item["check"].startswith("dataset:")
    ]
    if hard_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
