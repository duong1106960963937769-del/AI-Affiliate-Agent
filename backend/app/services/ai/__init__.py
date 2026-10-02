from ..app_settings import AI_PROVIDERS
from ...config import settings as env
from .base import AIProvider, AIProviderError
from .ollama import OllamaProvider


def get_provider(general: dict, transport=None) -> AIProvider:
    name = general["ai_provider"]
    if name == "ollama":
        return OllamaProvider(env.ollama_url, general["ollama_model"], transport=transport)
    raise AIProviderError("provider_unavailable", f"Nhà cung cấp '{name}' chưa được triển khai (có thể tính phí).")


__all__ = ["AIProvider", "AIProviderError", "OllamaProvider", "get_provider", "AI_PROVIDERS"]
