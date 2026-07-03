# Evaluation Dataset

Use the synthetic dataset as a labeled CSV with one row per image.

Required columns:

- `image`: relative or absolute path to a single selfie-with-document image.
- `label`: `match` for a valid identity match, `no_match` for a mismatch.

Relative image paths are resolved from the directory that contains the CSV file.

Example:

```csv
image,label
dataset/person_001_match.jpg,match
dataset/person_002_mismatch.jpg,no_match
```

The project can compute accuracy, precision, recall, F1-score, and a confusion matrix only when the dataset contains both positive and negative examples. If the dataset contains only positive samples, report recall/success rate and explain that precision and false-positive behavior cannot be estimated.

If the dataset is organized as:

```text
dataset/
  match/
    image_001.jpg
  no_match/
    image_002.jpg
```

generate `samples.csv` with:

```powershell
python scripts/build_dataset_csv.py dataset --output samples.csv
```

Validation command:

```powershell
python scripts/validate_dataset.py samples.csv
```

Evaluation command:

```powershell
python evaluate.py samples.csv --threshold 0.363 --output evaluation_results.json --report docs/evaluation_report.md --plots-dir docs/figures --update-technical-analysis
python scripts/export_technical_pdf.py
```

Generated figures:

- `docs/figures/confusion_matrix.png`
- `docs/figures/score_distribution.png`

When `python scripts/export_technical_pdf.py` is run, PNG files in `docs/figures/` are appended to the technical PDF automatically.

Optional threshold tuning:

```powershell
python scripts/tune_threshold.py samples.csv --output threshold_tuning.json
```

End-to-end final workflow:

```powershell
python scripts/finalize_submission.py --csv samples.csv --tune-threshold
```
