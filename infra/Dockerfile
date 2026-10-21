FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/app/data \
    WEB_CONCURRENCY=1 \
    EMBEDDING_BACKEND=fts \
    EMBEDDED_WORKER=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-hin \
    curl \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY . /app/

RUN mkdir -p /app/data

EXPOSE 8000 10000

CMD ["sh", "-c", "python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
