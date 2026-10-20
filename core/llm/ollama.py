import json
from typing import Any, Dict, List, Optional
import httpx
from apps.api.app.config import get_settings
from apps.api.app.logging import get_logger
from core.llm.base import BaseLLMProvider

logger = get_logger("core.llm.ollama")
settings = get_settings()


class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "llama3:latest", base_url: Optional[str] = None):
        self.model_name = model_name
        self.base_url = (base_url or settings.OLLAMA_URL).rstrip("/")

    def generate_json(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        schema: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "format": "json",
            "stream": False,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                raw_response = data.get("response", "{}")
                return json.loads(raw_response)
        except Exception as exc:
            logger.error(f"Ollama generation error: {exc}")
            raise
