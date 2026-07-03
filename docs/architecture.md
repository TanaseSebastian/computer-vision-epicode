# Architecture

## Runtime Components

```text
Browser / API Client
        |
        v
Flask routes (`app/routes.py`)
        |
        v
Vision pipeline (`app/vision.py`)
        |
        +--> Deep path: YuNet detection + SFace embeddings
        |
        +--> Classical fallback: Haar detection + LBP/gradient features
        |
        v
Result: score, decision, detected faces, annotated preview
```

## Single-Image Assumption

The dataset contains one image per sample: a person holding an identity document. The pipeline assumes:

- the largest detected face is the live/selfie face;
- smaller detected faces are document-face candidates;
- the best similarity score among document candidates is used for the final decision.

This assumption is simple, explainable, and appropriate for the synthetic dataset. It can fail when the document face is not detected, when another large face appears in the background, or when the live face is not the largest detected face.

## Data Flow

1. `POST /verify` or `POST /api/verify` receives `identity_image`.
2. The uploaded file is saved temporarily in `app/uploads/`.
3. OpenCV decodes the image.
4. The deep detector finds face candidates.
5. SFace extracts embeddings and computes cosine similarity.
6. If the deep path is unavailable, the classical fallback is used.
7. The file is deleted in the Flask `finally` block.
8. The web route renders HTML; the API route returns JSON.

The `/health` endpoint reports service status and model-file availability.

## Extension Points

- Replace largest-face heuristic with document detection or segmentation.
- Add OCR/document localization for stronger document-region constraints.
- Fine-tune or compare alternative face-recognition backbones.
- Add calibrated thresholds per dataset split.
- Add liveness checks if the project is extended beyond academic demonstration.
