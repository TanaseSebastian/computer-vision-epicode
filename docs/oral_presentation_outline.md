# Oral Presentation Outline

## 1. Project Goal

Explain the problem: identity verification from one selfie where the user holds a visible document.

## 2. Dataset

Describe the synthetic dataset, labels (`match` and `no_match`), and why both classes are needed for precision, recall, F1-score, and confusion matrix.

## 3. Pipeline

Walk through:

1. image upload;
2. face detection;
3. largest-face selection as live/selfie face;
4. smaller faces as document candidates;
5. embedding extraction;
6. cosine similarity;
7. threshold decision;
8. annotated preview.

## 4. Algorithms

Discuss YuNet and SFace as the deep-learning pipeline. Then explain the classical fallback: Haar Cascade, histogram equalization, LBP, gradient histogram, and cosine similarity.

## 5. Evaluation

Show the commands:

```powershell
python scripts/validate_dataset.py samples.csv
python scripts/tune_threshold.py samples.csv --output threshold_tuning.json
python evaluate.py samples.csv --threshold 0.36 --output evaluation_results.json --report docs/evaluation_report.md --update-technical-analysis
```

Explain accuracy, precision, recall, F1-score, and confusion matrix.

## 6. Failure Analysis

Mention small document portraits, blur, glare, occlusion, unrelated faces, wrong largest-face assumption, and synthetic-to-real domain gap.

## 7. Ethics

Discuss privacy, deletion of uploads, no storage of biometric data, bias risks, and why this is an academic prototype rather than a real identity-control system.

## 8. Demo

Open the Flask app, upload one selfie-with-document image, show the match/no-match score and annotated preview.
