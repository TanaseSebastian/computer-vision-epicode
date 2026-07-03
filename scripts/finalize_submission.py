import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run(command: list[str]) -> None:
    print(">", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description="Run the final submission workflow.")
    parser.add_argument("--dataset-dir", type=Path, help="Optional dataset folder used to rebuild samples.csv.")
    parser.add_argument("--csv", type=Path, default=Path("samples.csv"))
    parser.add_argument("--threshold", type=float, default=0.363)
    parser.add_argument("--tune-threshold", action="store_true")
    args = parser.parse_args()

    python = sys.executable

    if args.dataset_dir:
        run([python, "scripts/build_dataset_csv.py", str(args.dataset_dir), "--output", str(args.csv)])

    run([python, "scripts/validate_dataset.py", str(args.csv)])

    threshold = args.threshold
    if args.tune_threshold:
        tuning_output = ROOT / "threshold_tuning.json"
        run([python, "scripts/tune_threshold.py", str(args.csv), "--output", str(tuning_output)])
        report = json.loads(tuning_output.read_text(encoding="utf-8"))
        threshold = report["best"]["threshold"]
        print(f"Using tuned threshold: {threshold}")

    run(
        [
            python,
            "evaluate.py",
            str(args.csv),
            "--threshold",
            str(threshold),
            "--output",
            "evaluation_results.json",
            "--report",
            "docs/evaluation_report.md",
            "--plots-dir",
            "docs/figures",
            "--update-technical-analysis",
        ]
    )
    run([python, "scripts/export_technical_pdf.py"])
    run([python, "-B", "-m", "pytest", "-q"])
    run([python, "scripts/project_audit.py"])

    print("Final submission workflow complete.")


if __name__ == "__main__":
    main()
