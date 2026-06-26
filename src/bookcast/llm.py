from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


class LlmProvider:
    id = "base"

    def health(self) -> bool:
        raise NotImplementedError

    def generate(self, prompt: str, mode: str = "json") -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class OllamaProvider(LlmProvider):
    model: str = "qwen3:8b"
    base_url: str = "http://127.0.0.1:11434"
    timeout_sec: int = 120
    keep_alive: str | int = -1

    id = "ollama"

    def health(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5) as response:
                return response.status == 200
        except (OSError, urllib.error.URLError):
            return False

    def generate(self, prompt: str, mode: str = "json") -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json" if mode == "json" else "",
            "keep_alive": self.keep_alive,
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        return str(data.get("response", "")).strip()


def parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response did not contain a JSON object")
    return json.loads(text[start : end + 1])
