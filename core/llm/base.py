from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        schema: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates structured JSON response adhering to schema."""
        pass
