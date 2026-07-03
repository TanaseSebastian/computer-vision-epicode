# Submission Checklist

Before publishing or submitting:

- Run `pytest`.
- Run `python scripts/project_audit.py`.
- On Windows, the same checks can be run with `.\scripts\windows\check.ps1`.
- Run `python scripts/download_models.py` before the live demo if the `models/` folder is empty.
- Put the real dataset images in a local `dataset/` folder or update `samples.csv` with the correct paths.
- If the dataset uses `dataset/match/` and `dataset/no_match/`, run `python scripts/build_dataset_csv.py dataset --output samples.csv`.
- Run `python scripts/validate_dataset.py samples.csv`.
- Optionally tune the threshold with `python scripts/tune_threshold.py samples.csv --output threshold_tuning.json`.
- Run `python evaluate.py samples.csv --threshold 0.36 --output evaluation_results.json --report docs/evaluation_report.md --plots-dir docs/figures --update-technical-analysis`.
- On Windows, the evaluation flow can be run with `.\scripts\windows\evaluate_dataset.ps1 -CsvPath samples.csv -Threshold 0.36`.
- Cross-platform final workflow: `python scripts/finalize_submission.py --csv samples.csv --tune-threshold`.
- Create a clean submission ZIP with `python scripts/package_submission.py`.
- Run `python scripts/export_technical_pdf.py`.
- Check that `docs/technical_analysis.pdf` includes real results, not placeholder values.
- Create or update the public GitHub repository.
- Make sure the repository includes source code, README, requirements, technical PDF, and documentation.
- Check that GitHub Actions runs the test workflow successfully.
- If Docker is required, run `docker build -t identity-checker .`.
- Review `docs/architecture.md` and `docs/api.md`.
- Review `docs/oral_presentation_outline.md` before the oral exam.
- Review `docs/privacy_and_ethics.md` for the ethics section.
- Review `docs/model_card.md` and `docs/references.md` for model justification.
- Do not commit private identity documents, real personal data, `.venv/`, `.tools/`, or ONNX model binaries unless explicitly allowed.

Recommended final repository contents:

- `app/`
- `docs/`
- `openapi.json`
- `Dockerfile`
- `.dockerignore`
- `scripts/`
- `tests/`
- `.github/workflows/tests.yml`
- `evaluate.py`
- `requirements.txt`
- `README.md`
- `samples.csv`
