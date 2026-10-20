import hashlib
import hmac
import os
import time
from pathlib import Path
from typing import Generator, Optional, Tuple
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from apps.api.app.config import get_settings

settings = get_settings()


def get_data_dir() -> Path:
    p = Path(settings.DATA_DIR).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_video_dir(video_id: str) -> Path:
    p = get_data_dir() / "videos" / str(video_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_original_path(video_id: str, ext: str = ".mp4") -> Path:
    return get_video_dir(video_id) / f"original{ext}"


def get_proxy_path(video_id: str) -> Path:
    return get_video_dir(video_id) / "proxy.mp4"


def get_audio_path(video_id: str) -> Path:
    return get_video_dir(video_id) / "audio.wav"


def generate_stream_token(video_id: str, expires_in_s: int = 3600) -> str:
    expires_at = int(time.time()) + expires_in_s
    payload = f"{video_id}:{expires_at}"
    sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_stream_token(video_id: str, token: str) -> bool:
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return False
        token_vid, expires_at_str, sig = parts
        if token_vid != str(video_id):
            return False
        expires_at = int(expires_at_str)
        if time.time() > expires_at:
            return False
        payload = f"{token_vid}:{expires_at_str}"
        expected_sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False


def range_streaming_response(request: Request, file_path: Path, media_type: str = "video/mp4") -> Response:
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Media file not found")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("Range")

    if not range_header or not range_header.startswith("bytes="):
        # Full content response
        def full_file_iterator(chunk_size: int = 1024 * 1024):
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    yield chunk

        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": media_type,
        }
        return StreamingResponse(full_file_iterator(), status_code=200, headers=headers)

    # Range request handling (206)
    range_str = range_header.replace("bytes=", "").strip()
    range_parts = range_str.split("-")
    try:
        start = int(range_parts[0]) if range_parts[0] else 0
        end = int(range_parts[1]) if len(range_parts) > 1 and range_parts[1] else file_size - 1
    except ValueError:
        raise HTTPException(status_code=416, detail="Invalid Range header")

    if start >= file_size or end >= file_size or start > end:
        raise HTTPException(
            status_code=416,
            detail="Requested range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    content_length = end - start + 1

    def range_file_iterator(start_byte: int, end_byte: int, chunk_size: int = 1024 * 1024):
        with open(file_path, "rb") as f:
            f.seek(start_byte)
            remaining = end_byte - start_byte + 1
            while remaining > 0:
                bytes_to_read = min(remaining, chunk_size)
                data = f.read(bytes_to_read)
                if not data:
                    break
                remaining -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": media_type,
    }
    return StreamingResponse(
        range_file_iterator(start, end),
        status_code=206,
        headers=headers,
    )
