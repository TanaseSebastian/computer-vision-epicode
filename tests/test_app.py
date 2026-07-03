import csv
import json
from pathlib import Path

import numpy as np
import pytest

from app import create_app
from evaluate import save_plots
from app.vision import cosine_similarity, local_binary_pattern
from scripts.build_dataset_csv import build_rows
from scripts.tune_threshold import metrics_for_threshold
from scripts.validate_dataset import validate


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_index_uses_single_image_upload(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Selfie con documento" in response.data
    assert b"Foto documento" not in response.data


def test_verify_requires_file(client):
    response = client.post("/verify", data={})

    assert response.status_code == 400
    assert b"Carica una foto selfie" in response.data


def test_api_verify_requires_file(client):
    response = client.post("/api/verify", data={})

    assert response.status_code == 400
    assert response.get_json()["error"].startswith("Carica una foto selfie")


def test_health_endpoint(client):
    response = client.get("/health")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert "yunet" in payload["models"]
    assert "sface" in payload["models"]


def test_cosine_similarity_bounds():
    assert cosine_similarity(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == 1.0
    assert cosine_similarity(np.array([1.0, 0.0]), np.array([-1.0, 0.0])) == 0.0


def test_lbp_histogram_shape_and_normalization():
    image = np.arange(100, dtype=np.uint8).reshape(10, 10)
    hist = local_binary_pattern(image)

    assert hist.shape == (256,)
    assert np.isclose(hist.sum(), 1.0)


def test_validate_dataset_accepts_existing_files(tmp_path: Path):
    image_path = tmp_path / "sample.jpg"
    image_path.write_bytes(b"not a real image, validation checks existence only")
    csv_path = tmp_path / "samples.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image", "label"])
        writer.writeheader()
        writer.writerow({"image": str(image_path), "label": "match"})
        writer.writerow({"image": str(image_path), "label": "no_match"})

    errors, counts = validate(csv_path)

    assert errors == []
    assert counts["rows"] == 2
    assert counts["positive"] == 1
    assert counts["negative"] == 1


def test_validate_dataset_resolves_paths_relative_to_csv(tmp_path: Path):
    dataset_dir = tmp_path / "dataset"
    config_dir = tmp_path / "config"
    dataset_dir.mkdir()
    config_dir.mkdir()
    image_path = dataset_dir / "sample.jpg"
    image_path.write_bytes(b"placeholder")
    csv_path = config_dir / "samples.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image", "label"])
        writer.writeheader()
        writer.writerow({"image": "../dataset/sample.jpg", "label": "match"})
        writer.writerow({"image": "../dataset/sample.jpg", "label": "no_match"})

    errors, counts = validate(csv_path)

    assert errors == []
    assert counts["missing_files"] == 0


def test_build_dataset_csv_infers_labels_from_folders(tmp_path: Path):
    positive_dir = tmp_path / "match"
    negative_dir = tmp_path / "no_match"
    positive_dir.mkdir()
    negative_dir.mkdir()
    (positive_dir / "a.jpg").write_bytes(b"x")
    (negative_dir / "b.png").write_bytes(b"x")

    rows = build_rows(tmp_path)

    assert rows == [
        {"image": str(positive_dir / "a.jpg"), "label": "match"},
        {"image": str(negative_dir / "b.png"), "label": "no_match"},
    ]


def test_threshold_metrics_selects_expected_predictions():
    rows = [
        {"expected": True, "score": 0.8},
        {"expected": False, "score": 0.2},
    ]

    metrics = metrics_for_threshold(rows, 0.5)

    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0


def test_openapi_documents_api_verify():
    spec = json.loads(Path("openapi.json").read_text(encoding="utf-8"))

    assert spec["openapi"].startswith("3.")
    assert "/api/verify" in spec["paths"]
    assert "post" in spec["paths"]["/api/verify"]
    assert "/health" in spec["paths"]


def test_model_download_script_exists():
    assert Path("scripts/download_models.py").exists()


def test_docker_deployment_files_exist():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert "EXPOSE 5000" in dockerfile
    assert 'CMD ["python", "-B", "-m", "app"]' in dockerfile
    assert ".venv/" in dockerignore
    assert "dataset/" in dockerignore


def test_model_documentation_exists():
    assert Path("docs/model_card.md").exists()
    assert Path("docs/references.md").exists()


def test_windows_helper_scripts_exist():
    assert Path("scripts/windows/setup.ps1").exists()
    assert Path("scripts/windows/check.ps1").exists()
    assert Path("scripts/windows/evaluate_dataset.ps1").exists()


def test_finalize_submission_script_exists():
    assert Path("scripts/finalize_submission.py").exists()


def test_package_submission_script_exists():
    assert Path("scripts/package_submission.py").exists()


def test_pdf_export_supports_figures():
    export_script = Path("scripts/export_technical_pdf.py").read_text(encoding="utf-8")

    assert "FIGURES_DIR" in export_script
    assert "glob(\"*.png\")" in export_script


def test_save_plots_creates_png_files(tmp_path: Path):
    report = {
        "confusion_matrix": {
            "true_positive": 1,
            "true_negative": 1,
            "false_positive": 0,
            "false_negative": 0,
        },
        "rows": [
            {"expected": True, "score": 0.8},
            {"expected": False, "score": 0.2},
        ],
    }

    save_plots(report, tmp_path)

    assert (tmp_path / "confusion_matrix.png").exists()
    assert (tmp_path / "score_distribution.png").exists()
