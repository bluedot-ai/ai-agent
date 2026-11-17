import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    backend: str
    model: str
    key: str
    base_url: str | None
    api: str

    @classmethod
    def load(cls):
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise ValueError("缺少 OPENAI_API_KEY；未执行模型推理")
        api = os.getenv("AGENT_MODEL_API", "responses")
        if api not in {"responses", "chat_completions"}:
            raise ValueError("AGENT_MODEL_API 无效")
        return cls(os.getenv("DEVSTART_BASE_URL", "http://localhost:8080"),
                   os.getenv("AGENT_MODEL", "gpt-4.1-mini"), key,
                   os.getenv("OPENAI_BASE_URL") or None, api)
