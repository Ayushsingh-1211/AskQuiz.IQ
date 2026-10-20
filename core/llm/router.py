from typing import Any, Dict, List, Optional
from apps.api.app.config import get_settings
from apps.api.app.logging import get_logger
from core.cache import compute_content_hash, get_cached, set_cached
from core.llm.gemini import GeminiProvider
from core.llm.ollama import OllamaProvider

logger = get_logger("core.llm.router")
settings = get_settings()

CALL_COUNTERS: Dict[str, int] = {}


def get_call_count(model_name: str) -> int:
    return CALL_COUNTERS.get(model_name, 0)


def increment_call_count(model_name: str) -> None:
    CALL_COUNTERS[model_name] = CALL_COUNTERS.get(model_name, 0) + 1


def route_generate_json(
    prompt: str,
    images: Optional[List[str]] = None,
    schema: Optional[Dict[str, Any]] = None,
    system_instruction: Optional[str] = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Hard rule 7: All LLM calls go through core/llm/router.py (cache, caps, fallback, counter).
    """
    cache_key = compute_content_hash(prompt, images or [], system_instruction or "")
    if use_cache:
        cached = get_cached(cache_key)
        if cached:
            logger.info("Serving LLM response from content-hash cache")
            return cached

    # Parse fallback chain
    chain_str = settings.LLM_FALLBACK_CHAIN or f"{settings.ANSWER_MODEL},{settings.VISION_MODEL},ollama"
    chain = [m.strip() for m in chain_str.split(",") if m.strip()]
    if not chain:
        chain = ["gemini", "ollama"]

    last_error: Optional[Exception] = None

    for target in chain:
        daily_cap = settings.LLM_DAILY_CAP
        if daily_cap > 0 and get_call_count(target) >= daily_cap:
            logger.warning(f"Daily cap reached for model {target} ({get_call_count(target)} calls), trying fallback")
            continue

        try:
            if target == "ollama":
                provider = OllamaProvider()
            else:
                provider = GeminiProvider(model_name=target if target != "gemini" else None)

            result = provider.generate_json(
                prompt=prompt,
                images=images,
                schema=schema,
                system_instruction=system_instruction,
            )
            increment_call_count(target)
            if use_cache:
                set_cached(cache_key, result)
            return result

        except Exception as exc:
            logger.warning(f"LLM call to {target} failed: {exc}. Trying next in fallback chain.")
            last_error = exc

    # Retrieval-only degradation fallback
    logger.error(f"All LLM providers in fallback chain failed. Last error: {last_error}")
    return {
        "answer": "Free quota reached, retrying in 30s.",
        "citations": [],
        "confidence": "low",
        "refusal": True,
        "notes": "Degraded to retrieval-only",
        "used_pause_frame": False,
    }
