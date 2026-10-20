import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Response, status
from apps.api.app.config import get_settings
from apps.api.app.db.session import check_db_health
from apps.api.app.logging import get_logger

logger = get_logger("apps.api.health")
router = APIRouter(prefix="/api/v1", tags=["health"])

_cached_embed_model: Optional[Any] = None


def check_ffmpeg() -> Dict[str, Any]:
    settings = get_settings()
    cmd = settings.resolved_ffmpeg_cmd()
    try:
        res = subprocess.run([cmd, "-version"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0] if res.stdout else "ffmpeg available"
            return {"ok": True, "detail": first_line}
        return {"ok": False, "detail": f"Exit code {res.returncode}: {res.stderr[:200]}"}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)}


def check_ffprobe() -> Dict[str, Any]:
    settings = get_settings()
    cmd = settings.resolved_ffprobe_cmd()
    try:
        res = subprocess.run([cmd, "-version"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0] if res.stdout else "ffprobe available"
            return {"ok": True, "detail": first_line}
        return {"ok": False, "detail": f"Exit code {res.returncode}: {res.stderr[:200]}"}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)}


def check_tesseract() -> Dict[str, Any]:
    settings = get_settings()
    cmd = settings.resolved_tesseract_cmd()
    try:
        res = subprocess.run([cmd, "--list-langs"], capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            return {"ok": False, "detail": f"Exit code {res.returncode}: {res.stderr[:200]}"}
        langs = [line.strip() for line in res.stdout.splitlines() if line.strip() and not line.startswith("List of")]
        has_eng = "eng" in langs
        has_hin = "hin" in langs
        if has_eng and has_hin:
            return {"ok": True, "langs": langs}
        missing = []
        if not has_eng:
            missing.append("eng")
        if not has_hin:
            missing.append("hin")
        return {"ok": False, "detail": f"Missing required languages: {', '.join(missing)}", "langs": langs}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)}


def check_data_dir() -> Dict[str, Any]:
    settings = get_settings()
    data_path = Path(settings.DATA_DIR).resolve()
    try:
        data_path.mkdir(parents=True, exist_ok=True)
        test_file = data_path / ".health_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return {"ok": True, "path": str(data_path)}
    except Exception as exc:
        return {"ok": False, "detail": str(exc), "path": str(data_path)}


def check_gemini_key() -> Dict[str, Any]:
    settings = get_settings()
    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
        return {"ok": True, "detail": "configured"}
    return {"ok": False, "detail": "GEMINI_API_KEY is not configured or empty"}


def check_embed_model() -> Dict[str, Any]:
    global _cached_embed_model
    settings = get_settings()
    model_name = settings.EMBED_MODEL
    try:
        if _cached_embed_model is None:
            from sentence_transformers import SentenceTransformer
            _cached_embed_model = SentenceTransformer(model_name)
        return {"ok": True, "model": model_name}
    except Exception as exc:
        return {"ok": False, "detail": str(exc), "model": model_name}


def run_all_self_checks() -> Dict[str, Any]:
    checks = {
        "ffmpeg": check_ffmpeg(),
        "ffprobe": check_ffprobe(),
        "tesseract": check_tesseract(),
        "database": {"ok": check_db_health()},
        "data_dir": check_data_dir(),
        "gemini_key": check_gemini_key(),
        "embed_model": check_embed_model(),
    }
    all_ok = all(check["ok"] for check in checks.values())
    status_str = "ok" if all_ok else "degraded"
    return {
        "status": status_str,
        "checks": checks,
    }


@router.get("/health")
def health(response: Response) -> Dict[str, Any]:
    results = run_all_self_checks()
    if results["status"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return results
