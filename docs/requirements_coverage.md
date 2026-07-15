# Requirements Coverage

| Requirement from exam brief | Project evidence |
| --- | --- |
| Complete Computer Vision application | Flask app in `app/` with upload, inference, result page, and annotated preview |
| Real-world problem | Identity verification from a selfie with visible document |
| Data acquisition and preprocessing | Upload route in `app/routes.py`; image decoding, face detection, crop/alignment in `app/vision.py` |
| Feature engineering or representation | SFace embeddings plus classical fallback using grayscale, LBP, and gradient histograms |
| Core model logic | YuNet/SFace deep pipeline and Haar/LBP fallback in `app/vision.py` |
| Post-processing | Largest-face selection, best document candidate selection, thresholding, annotated preview |
| Python and industry-standard libraries | Python, Flask, OpenCV, NumPy, Pillow in `requirements.txt` |
| Model setup reproducibility | `scripts/download_models.py` and documented OpenCV Zoo model files |
| Modular and documented code | Separate Flask routes, vision pipeline, evaluation script, docs |
| Pre-trained models justified and combined with custom logic | Explained in `docs/technical_analysis.md`; custom single-image candidate selection and fallback |
| Model documentation | `docs/model_card.md` and `docs/references.md` |
| Performance evaluation | `evaluate.py` computes accuracy, precision, recall, F1-score, confusion matrix, and plots |
| Reproducible experimental workflow | `scripts/build_dataset_csv.py`, `scripts/validate_dataset.py`, `scripts/tune_threshold.py`, `samples.csv`, `docs/evaluation_dataset.md`, generated evaluation report |
| Final submission workflow | `scripts/finalize_submission.py` |
| One-command Windows workflow | `scripts/windows/setup.ps1`, `scripts/windows/check.ps1`, `scripts/windows/evaluate_dataset.ps1` |
| Submission readiness | `scripts/project_audit.py` and `docs/submission_checklist.md` |
| Repository deliverables | Source code, `requirements.txt`, `README.md`, technical analysis Markdown and PDF |
| Failure analysis | `docs/technical_analysis.md` section 7 |
| Ethical considerations | `docs/technical_analysis.md` section 8 |
| Security and privacy best practices | Upload deletion in `app/routes.py`, size limit in `app/__init__.py`, `docs/privacy_and_ethics.md` |
| Optional web app/API | Flask web application and `/api/verify` JSON endpoint |
| Optional deployment | `Dockerfile`, `.dockerignore`, and `docs/deployment.md` |
| API documentation | `docs/api.md` and `openapi.json` |
| Architecture documentation | `docs/architecture.md` |
| Automated quality checks | `tests/` pytest suite |
| CI-ready repository | `.github/workflows/tests.yml` |
| Oral examination preparation | `docs/oral_presentation_outline.md` |
