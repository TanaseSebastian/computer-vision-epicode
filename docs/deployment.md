# Deployment

## Local Flask

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/download_models.py
python -m app
```

Open `http://127.0.0.1:5000`.

Health check:

```powershell
curl http://127.0.0.1:5000/health
```

Windows shortcut:

```powershell
.\scripts\windows\setup.ps1
.\.venv\Scripts\python.exe -B -m app
```

## Docker

Build:

```powershell
docker build -t identity-checker .
```

Run:

```powershell
docker run --rm -p 5000:5000 identity-checker
```

Open `http://127.0.0.1:5000`.

## Notes

The Docker image downloads the OpenCV Zoo ONNX models during build. Do not copy real datasets, private documents, or generated evaluation outputs into the image.
