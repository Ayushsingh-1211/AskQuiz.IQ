import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from apps.api.app.config import get_settings
from apps.api.app.logging import get_logger
from core.llm.base import BaseLLMProvider

logger = get_logger("core.llm.gemini")
settings = get_settings()


class GeminiProvider(BaseLLMProvider):
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.ANSWER_MODEL or "gemini-2.5-flash"
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_json(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        schema: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        contents: List[Any] = []

        if images:
            for img_path in images:
                p = Path(img_path)
                if p.exists():
                    img_bytes = p.read_bytes()
                    mime = "image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"
                    contents.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))

        contents.append(prompt)

        config_kwargs: Dict[str, Any] = {
            "response_mime_type": "application/json",
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_kwargs)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            raw_text = response.text or "{}"
            return json.loads(raw_text)
        except json.JSONDecodeError as jde:
            logger.warning(f"Gemini response not valid JSON: {raw_text[:200]}")
            # Try extracting json block
            import re
            m = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if m:
                return json.loads(m.group(0))
            raise
        except Exception as exc:
            logger.error(f"Gemini generation error: {exc}")
            raise
