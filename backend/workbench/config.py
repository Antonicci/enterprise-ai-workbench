from typing import Literal
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    provider: Literal["demo", "ollama", "openai-compatible"] = "demo"
    store: Literal["memory", "postgres"] = "memory"
    ollama_base_url: str = "http://localhost:11434"
    chat_model: str = "qwen2.5:3b"
    embedding_model: str = "nomic-embed-text"
    api_base_url: str = "https://example.invalid/v1"
    api_key: SecretStr = SecretStr("")
    database_url: SecretStr = SecretStr("postgresql://workbench:workbench@localhost:5432/workbench")
    # Static credentials are a LAB boundary; replace with verified OIDC in production.
    auth_tokens: dict[str, list[str]] = Field(default_factory=lambda: {
        "demo-analyst": ["employees"], "demo-ops": ["employees", "operations"]
    })
    request_timeout: float = Field(default=60, gt=0, le=180)
    top_k: int = Field(default=4, ge=1, le=10)
    @model_validator(mode="after")
    def validate_mode(self):
        if self.provider != "demo" and any(k.startswith("demo-") for k in self.auth_tokens):
            raise ValueError("Replace demo credentials in AUTH_TOKENS before enabling real providers")
        if not self.auth_tokens or any(not k or not v for k,v in self.auth_tokens.items()):
            raise ValueError("Configure at least one nonempty token and group")
        if self.provider == "openai-compatible" and not self.api_key.get_secret_value():
            raise ValueError("API_KEY is required for openai-compatible")
        return self
    @property
    def namespace(self):
        return "demo-hash-v1" if self.provider == "demo" else f"{self.provider}:{self.embedding_model}"
