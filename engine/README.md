# Moderation Engine

FastAPI service that exposes HTTP endpoints for content moderation.

## Endpoints

| Method | Path              | Description                |
|--------|-------------------|----------------------------|
| POST   | `/moderate_text`  | Classify plain text        |
| POST   | `/moderate_image` | Classify an image          |
| POST   | `/moderate_video` | Classify a video (stub)    |
| GET    | `/health`         | Health check               |

## Setup

```bash
cd engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit thresholds if needed
python main.py
```

The API will be available at `http://localhost:8000`.

## Deepfake Detection

> **Warning:** The `detect_deepfake_suspect` function is currently a **stub**
> that returns a fixed score of `0.05`. Replace it with a real model (e.g.
> EfficientNet fine-tuned on FaceForensics++) before using in production.
