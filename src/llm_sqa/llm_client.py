from __future__ import annotations

import json
import logging
from typing import Any

import requests

from llm_sqa.config import get_settings

logger = logging.getLogger(__name__)


class OllamaUnavailableError(RuntimeError):
    """Raised when the local Ollama service is not reachable."""


class OllamaClient:
    def __init__(
        self, host: str | None = None, model: str | None = None, timeout: int = 120
    ) -> None:
        settings = get_settings()
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return bool(response.ok)
        except requests.RequestException:
            return False

    def generate_json(self, prompt: str) -> dict[str, Any]:
        if not self.is_available():
            raise OllamaUnavailableError(
                f"Ollama is not reachable at {self.host}. Start Ollama or use deterministic fallback."
            )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_ctx": 8192,
            },
        }
        logger.info("Calling Ollama model=%s", self.model)
        response = requests.post(f"{self.host}/api/generate", json=payload, timeout=self.timeout)
        response.raise_for_status()
        body = response.json()
        raw_text = body.get("response", "")
        return _load_json_object(str(raw_text))


def _load_json_object(raw_text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"LLM response did not contain a JSON object: {raw_text[:200]}")

    parsed = json.loads(raw_text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON root must be an object.")
    return parsed
