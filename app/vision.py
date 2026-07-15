import base64
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlretrieve

import cv2
import numpy as np


class VerificationError(Exception):
    """Raised when an uploaded image cannot be used for verification."""


@dataclass
class VerificationResult:
    match: bool
    score: float
    threshold: float
    total_faces: int
    candidate_document_faces: int
    method: str
    classical_score: float | None
    deep_score: float | None
    annotated_image: str | None
    message: str


CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
FACE_CASCADE = cv2.CascadeClassifier(CASCADE_PATH)
if FACE_CASCADE.empty():
    raise RuntimeError("OpenCV non ha caricato il classificatore Haar Cascade per i volti.")

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT_DIR / "models"
YUNET_MODEL = MODEL_DIR / "face_detection_yunet_2023mar.onnx"
SFACE_MODEL = MODEL_DIR / "face_recognition_sface_2021dec.onnx"
MODEL_URLS = {
    YUNET_MODEL: "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx?download=true",
    SFACE_MODEL: "https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx?download=true",
}


def read_image(path: Path) -> np.ndarray:
    if not path.exists():
        raise VerificationError(f"Immagine non trovata: {path}")

    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise VerificationError("Una delle immagini non puo essere letta.")
    return image


def detect_faces(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = FACE_CASCADE.detectMultiScale(
        gray,
        scaleFactor=1.08,
        minNeighbors=5,
        minSize=(32, 32),
    )
    return sorted(faces, key=lambda box: box[2] * box[3], reverse=True)


def crop_face(image: np.ndarray, faces: list[tuple[int, int, int, int]]) -> np.ndarray:
    if not faces:
        raise VerificationError("Non ho trovato un volto chiaro in una delle immagini.")

    x, y, w, h = faces[0]
    pad_x = int(w * 0.18)
    pad_y = int(h * 0.25)
    x1 = max(x - pad_x, 0)
    y1 = max(y - pad_y, 0)
    x2 = min(x + w + pad_x, image.shape[1])
    y2 = min(y + h + pad_y, image.shape[0])
    return image[y1:y2, x1:x2]


def normalized_face(image: np.ndarray) -> np.ndarray:
    resized = cv2.resize(image, (160, 160), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    return gray


def local_binary_pattern(gray: np.ndarray) -> np.ndarray:
    center = gray[1:-1, 1:-1]
    codes = np.zeros_like(center, dtype=np.uint8)
    offsets = [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
        (1, 0),
        (1, -1),
        (0, -1),
    ]

    for bit, (dy, dx) in enumerate(offsets):
        neighbor = gray[1 + dy : gray.shape[0] - 1 + dy, 1 + dx : gray.shape[1] - 1 + dx]
        codes |= ((neighbor >= center) << bit).astype(np.uint8)

    hist, _ = np.histogram(codes.ravel(), bins=256, range=(0, 256), density=True)
    return hist.astype(np.float32)


def gradient_histogram(gray: np.ndarray) -> np.ndarray:
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitude, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)
    hist, _ = np.histogram(angle, bins=32, range=(0, 360), weights=magnitude, density=True)
    return np.nan_to_num(hist).astype(np.float32)


def standardized_unit_vector(values: np.ndarray) -> np.ndarray:
    centered = values.astype(np.float32) - float(values.mean())
    std = float(centered.std())
    if std > 1e-6:
        centered = centered / std

    norm = np.linalg.norm(centered)
    if norm == 0:
        return centered
    return centered / norm


def face_embedding(face: np.ndarray) -> np.ndarray:
    gray = normalized_face(face)
    small = cv2.resize(gray, (48, 48), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    features = np.concatenate(
        [
            standardized_unit_vector(small.ravel()) * 0.65,
            standardized_unit_vector(local_binary_pattern(gray)) * 0.20,
            standardized_unit_vector(gradient_histogram(gray)) * 0.15,
        ]
    )
    norm = np.linalg.norm(features)
    if norm == 0:
        raise VerificationError("Una delle immagini non contiene abbastanza dettagli utili.")
    return features / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    value = float(np.dot(a, b))
    return max(0.0, min(1.0, value))


def to_box(face: np.ndarray | tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x, y, w, h = face[:4]
    return int(x), int(y), int(w), int(h)


def annotated_image_data_uri(
    image: np.ndarray,
    selfie_box: tuple[int, int, int, int],
    document_box: tuple[int, int, int, int],
) -> str | None:
    preview = image.copy()
    for box, color, label in (
        (selfie_box, (28, 136, 91), "selfie"),
        (document_box, (217, 93, 57), "document"),
    ):
        x, y, w, h = box
        cv2.rectangle(preview, (x, y), (x + w, y + h), color, 3)
        cv2.putText(
            preview,
            label,
            (x, max(y - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
            cv2.LINE_AA,
        )

    ok, buffer = cv2.imencode(".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 86])
    if not ok:
        return None
    encoded = base64.b64encode(buffer).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def ensure_deep_models() -> bool:
    if not hasattr(cv2, "FaceDetectorYN_create") or not hasattr(cv2, "FaceRecognizerSF_create"):
        return False

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for path, url in MODEL_URLS.items():
        if not path.exists():
            try:
                urlretrieve(url, path)
            except Exception:
                return False

    if not YUNET_MODEL.exists() or not SFACE_MODEL.exists():
        return False

    try:
        cv2.FaceDetectorYN_create(str(YUNET_MODEL), "", (320, 320))
        cv2.FaceRecognizerSF_create(str(SFACE_MODEL), "")
    except cv2.error:
        return False

    return True


def deep_face_candidates(image: np.ndarray) -> list[np.ndarray]:
    if not ensure_deep_models():
        return []

    height, width = image.shape[:2]
    detector = cv2.FaceDetectorYN_create(
        str(YUNET_MODEL),
        "",
        (width, height),
        0.55,
        0.3,
        5000,
    )
    detector.setInputSize((width, height))
    _, faces = detector.detect(image)
    if faces is None or len(faces) == 0:
        return []

    return sorted(faces, key=lambda face: face[2] * face[3], reverse=True)


def deep_single_image_similarity(
    image: np.ndarray,
) -> tuple[float | None, int, int, tuple[int, int, int, int] | None, tuple[int, int, int, int] | None]:
    faces = deep_face_candidates(image)
    if len(faces) < 2:
        return None, len(faces), max(len(faces) - 1, 0), None, None

    recognizer = cv2.FaceRecognizerSF_create(str(SFACE_MODEL), "")
    selfie_face = faces[0]
    selfie_aligned = recognizer.alignCrop(image, selfie_face)
    selfie_feature = recognizer.feature(selfie_aligned)

    scores: list[tuple[float, np.ndarray]] = []
    for document_face in faces[1:]:
        document_aligned = recognizer.alignCrop(image, document_face)
        document_feature = recognizer.feature(document_aligned)
        score = recognizer.match(selfie_feature, document_feature, cv2.FaceRecognizerSF_FR_COSINE)
        scores.append((float(score), document_face))

    best_score, best_document_face = max(scores, key=lambda item: item[0])
    return best_score, len(faces), len(faces) - 1, to_box(selfie_face), to_box(best_document_face)


def classical_single_image_similarity(
    image: np.ndarray,
) -> tuple[float, int, int, tuple[int, int, int, int], tuple[int, int, int, int]]:
    faces = detect_faces(image)
    if len(faces) < 2:
        raise VerificationError("Servono almeno due volti nella foto: il volto della persona e quello sul documento.")

    selfie_face = crop_face(image, [faces[0]])
    selfie_embedding = face_embedding(selfie_face)

    scores: list[tuple[float, tuple[int, int, int, int]]] = []
    for face in faces[1:]:
        document_face = crop_face(image, [face])
        document_embedding = face_embedding(document_face)
        score = cosine_similarity(selfie_embedding, document_embedding)
        scores.append((score, face))

    best_score, best_document_face = max(scores, key=lambda item: item[0])
    return best_score, len(faces), len(faces) - 1, to_box(faces[0]), to_box(best_document_face)


def verify_identity(image_path: Path, threshold: float = 0.32) -> VerificationResult:
    if threshold <= 0 or threshold >= 1:
        raise VerificationError("La soglia deve essere compresa tra 0 e 1.")

    image = read_image(image_path)

    deep_score, deep_total_faces, deep_candidate_faces, deep_selfie_box, deep_document_box = deep_single_image_similarity(
        image,
    )
    try:
        (
            classical_score,
            classical_total_faces,
            classical_candidate_faces,
            classical_selfie_box,
            classical_document_box,
        ) = classical_single_image_similarity(image)
    except VerificationError:
        classical_score = None
        classical_total_faces = 0
        classical_candidate_faces = 0
        classical_selfie_box = None
        classical_document_box = None

    if deep_score is not None:
        score = deep_score
        method = "Deep learning: YuNet + SFace"
        total_faces = deep_total_faces
        candidate_document_faces = deep_candidate_faces
        selfie_box = deep_selfie_box
        document_box = deep_document_box
    else:
        if classical_score is None:
            raise VerificationError("Servono almeno due volti rilevabili nella stessa foto.")
        score = classical_score
        method = "Classical fallback: Haar + LBP/HOG-like features"
        total_faces = classical_total_faces
        candidate_document_faces = classical_candidate_faces
        selfie_box = classical_selfie_box
        document_box = classical_document_box

    match = score >= threshold

    message = (
        "Identita probabilmente verificata: il volto principale e il volto sul documento risultano compatibili."
        if match
        else "Identita non verificata: la somiglianza tra volto principale e documento e sotto la soglia scelta."
    )

    return VerificationResult(
        match=match,
        score=round(score, 3),
        threshold=threshold,
        total_faces=total_faces,
        candidate_document_faces=candidate_document_faces,
        method=method,
        classical_score=round(classical_score, 3) if classical_score is not None else None,
        deep_score=round(deep_score, 3) if deep_score is not None else None,
        annotated_image=annotated_image_data_uri(image, selfie_box, document_box)
        if selfie_box and document_box
        else None,
        message=message,
    )
