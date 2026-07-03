from pathlib import Path
from dataclasses import asdict
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

from .vision import SFACE_MODEL, YUNET_MODEL, VerificationError, verify_identity


bp = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(field_name: str) -> Path:
    file = request.files.get(field_name)
    if file is None or file.filename == "":
        raise VerificationError("Carica una foto selfie con il documento visibile.")

    if not allowed_file(file.filename):
        raise VerificationError("Formato non supportato. Usa JPG, PNG o WEBP.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    original_name = secure_filename(file.filename)
    suffix = Path(original_name).suffix.lower()
    destination = UPLOAD_DIR / f"{field_name}-{uuid4().hex}{suffix}"
    file.save(destination)
    return destination


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "models": {
                "yunet": YUNET_MODEL.exists(),
                "sface": SFACE_MODEL.exists(),
            },
        }
    )


@bp.post("/verify")
def verify():
    image_path = None

    try:
        image_path = save_upload("identity_image")
        try:
            threshold = float(request.form.get("threshold", 0.36))
        except ValueError as exc:
            raise VerificationError("La soglia deve essere un numero.") from exc

        result = verify_identity(image_path, threshold=threshold)
        return render_template("index.html", result=result, threshold=threshold)
    except VerificationError as exc:
        current_app.logger.info("Verification failed: %s", exc)
        return render_template("index.html", error=str(exc)), 400
    finally:
        if image_path and image_path.exists():
            image_path.unlink(missing_ok=True)


@bp.post("/api/verify")
def verify_api():
    image_path = None

    try:
        image_path = save_upload("identity_image")
        try:
            threshold = float(request.form.get("threshold", 0.36))
        except ValueError as exc:
            raise VerificationError("La soglia deve essere un numero.") from exc

        result = verify_identity(image_path, threshold=threshold)
        payload = asdict(result)
        payload.pop("annotated_image", None)
        return jsonify(payload)
    except VerificationError as exc:
        current_app.logger.info("API verification failed: %s", exc)
        return jsonify({"error": str(exc)}), 400
    finally:
        if image_path and image_path.exists():
            image_path.unlink(missing_ok=True)
