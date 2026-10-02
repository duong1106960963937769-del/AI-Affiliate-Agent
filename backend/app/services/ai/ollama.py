from __future__ import annotations

import logging
import time

import httpx

from .base import AIHealth, AIProvider, AIProviderError

log = logging.getLogger("api")

NOT_RUNNING = "Ollama is not running. Start Ollama and try again."


class OllamaProvider(AIProvider):
    name = "ollama"
    is_paid = False

    def __init__(self, base_url: str, model: str, transport: httpx.BaseTransport | None = None, timeout: float = 120.0):
        self.base_url, self.model = base_url.rstrip("/"), model
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout, transport=transport)

    def _request(self, method: str, path: str, **kw) -> httpx.Response:
        try:
            r = self._client.request(method, path, **kw)
        except httpx.ConnectError as e:
            raise AIProviderError("ollama_not_running", NOT_RUNNING, repr(e))
        except httpx.TimeoutException as e:
            raise AIProviderError("timeout", "Ollama phản hồi quá lâu. Model có thể đang được nạp, hãy thử lại sau ít phút.", repr(e))
        except httpx.HTTPError as e:
            raise AIProviderError("network_error", "Không giao tiếp được với Ollama.", repr(e))
        if r.status_code == 404 and "model" in r.text.lower():
            raise AIProviderError("model_missing", f"Chưa tải model '{self.model}'. Mở cmd và chạy: ollama pull {self.model}", r.text[:200])
        if r.status_code >= 400:
            raise AIProviderError("bad_status", f"Ollama trả lỗi {r.status_code}.", r.text[:200])
        return r

    def installed_models(self) -> list[str]:
        data = self._request("GET", "/api/tags").json()
        return [m.get("name", "") for m in data.get("models", []) if isinstance(m, dict)]

    def _has_model(self, installed: list[str]) -> bool:
        want = self.model if ":" in self.model else f"{self.model}:latest"
        return want in installed

    def test_connection(self) -> AIHealth:
        t0 = time.monotonic()
        installed = self.installed_models()  # ném ollama_not_running nếu tắt
        if not self._has_model(installed):
            raise AIProviderError("model_missing", f"Ollama đang chạy nhưng chưa có model '{self.model}'. "
                                  f"Mở cmd và chạy: ollama pull {self.model}")
        self.generate("Trả lời đúng một từ: OK")
        ms = int((time.monotonic() - t0) * 1000)
        return AIHealth(True, self.name, self.model, ms, "Kết nối Ollama thành công.", installed)

    def generate(self, prompt: str, system: str | None = None, json_mode: bool = False) -> str:
        body: dict = {"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0, "num_predict": 512}}
        if system:
            body["system"] = system
        if json_mode:
            body["format"] = "json"
        r = self._request("POST", "/api/generate", json=body)
        try:
            return str(r.json()["response"])
        except (ValueError, KeyError):
            raise AIProviderError("bad_response", "Ollama trả về dữ liệu không hợp lệ.", r.text[:200])
