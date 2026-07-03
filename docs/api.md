# API Documentation

## `GET /health`

Returns application status and whether the ONNX model files are available.

### Example

```powershell
curl http://127.0.0.1:5000/health
```

### Response

```json
{
  "status": "ok",
  "models": {
    "yunet": true,
    "sface": true
  }
}
```

## `POST /api/verify`

Verifies identity from a single selfie-with-document image.

### Request

Content type: `multipart/form-data`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `identity_image` | file | yes | JPG, JPEG, PNG, or WEBP image containing live face and document |
| `threshold` | number | no | Similarity threshold between 0 and 1. Default: `0.36` |

### Example

```powershell
curl -X POST http://127.0.0.1:5000/api/verify -F "identity_image=@dataset/sample.jpg" -F "threshold=0.36"
```

### Success Response

```json
{
  "match": true,
  "score": 0.51,
  "threshold": 0.36,
  "total_faces": 2,
  "candidate_document_faces": 1,
  "method": "Deep learning: YuNet + SFace",
  "classical_score": 0.42,
  "deep_score": 0.51,
  "message": "Identita probabilmente verificata: il volto principale e il volto sul documento risultano compatibili."
}
```

### Error Response

```json
{
  "error": "Carica una foto selfie con il documento visibile."
}
```

HTTP status code: `400`.
