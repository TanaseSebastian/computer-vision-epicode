import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "identity_checker_submission.zip"
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".tools",
    "__pycache__",
    ".pytest_cache",
    "models",
    "dataset",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_FILES = {
    "evaluation_results.json",
    "threshold_tuning.json",
    "identity_checker_submission.zip",
}


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if path.name in EXCLUDED_FILES:
        return False
    if relative.parts[:2] == ("app", "uploads") and path.name != ".gitkeep":
        return False
    if relative.parts[:2] == ("docs", "figures") and path.name != ".gitkeep":
        return False
    if relative.parts[:2] == ("docs",) and path.name == "evaluation_report.md":
        return False
    return path.is_file()


def create_package(output: Path) -> Path:
    output = output.resolve()
    if output.exists():
        output.unlink()

    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if path.resolve() == output:
                continue
            if should_include(path):
                archive.write(path, path.relative_to(ROOT))

    return output


def main():
    parser = argparse.ArgumentParser(description="Create a clean submission ZIP.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    output = create_package(args.output)
    print(output)


if __name__ == "__main__":
    main()
