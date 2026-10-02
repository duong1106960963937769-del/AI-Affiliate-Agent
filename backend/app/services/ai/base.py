"""Lớp trừu tượng AIProvider. Hiện chỉ có OllamaProvider (local, miễn phí).
Các provider trả phí (OpenAI/Gemini/Claude) CHƯA được triển khai và không được thêm khi chưa có xác nhận."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


class AIProviderError(Exception):
    """Lỗi AI với mã ổn định và thông báo thân thiện cho người dùng."""

    def __init__(self, code: str, user_message: str, technical: str | None = None):
        super().__init__(technical or user_message)
        self.code, self.user_message = code, user_message


@dataclass
class AIHealth:
    ok: bool
    provider: str
    model: str
    latency_ms: int | None
    message: str
    models_installed: list[str]


class AIProvider(ABC):
    name: str
    is_paid: bool = False

    @abstractmethod
    def test_connection(self) -> AIHealth: ...

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None, json_mode: bool = False) -> str: ...
