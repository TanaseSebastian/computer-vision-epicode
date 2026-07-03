import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.vision import MODEL_URLS, ensure_deep_models


def main():
    ready = ensure_deep_models()
    for path in MODEL_URLS:
        print(f"{path}: {'OK' if path.exists() else 'missing'}")

    if not ready:
        raise SystemExit("Deep models are not available. Check the network connection and try again.")

    print("Deep models ready.")


if __name__ == "__main__":
    main()
