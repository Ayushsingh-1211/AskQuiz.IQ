import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional
from apps.api.app.config import get_settings

settings = get_settings()


def get_cache_dir() -> Path:
    p = Path(settings.DATA_DIR).resolve() / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def compute_content_hash(*items: Any) -> str:
    hasher = hashlib.sha256()
    for item in items:
        if isinstance(item, (dict, list)):
            hasher.update(json.dumps(item, sort_keys=True, default=str).encode("utf-8"))
        else:
            hasher.update(str(item).encode("utf-8"))
    return hasher.hexdigest()


def get_cached(key: str) -> Optional[Dict[str, Any]]:
    path = get_cache_dir() / f"{key}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def set_cached(key: str, value: Dict[str, Any]) -> None:
    path = get_cache_dir() / f"{key}.json"
    try:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
