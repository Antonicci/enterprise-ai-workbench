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
    auth_mode: Literal["demo", "oidc"] = "demo"
    oidc_issuer: str = "http://localhost:8180/realms/workbench"
    oidc_jwks_url: str = "http://localhost:8180/realms/workbench/protocol/openid-connect/certs"
    oidc_audience: str = "workbench-api"
    oidc_client_id: str = "workbench-web"
    oidc_scope: str = "openid profile email"
    oidc_roles_claim: str = "realm_access.roles"
    # Public demo tokens are disabled entirely in OIDC mode.
    auth_tokens: dict[str, list[str]] = Field(default_factory=lambda: {
        "demo-analyst": ["query-l1"], "demo-ops": ["query-l2"],
        "demo-manager": ["knowledge-manager"]
    })
    request_timeout: float = Field(default=60, gt=0, le=180)
    top_k: int = Field(default=4, ge=1, le=10)
    @model_validator(mode="after")
    def validate_mode(self):
        if self.auth_mode == "demo" and self.provider != "demo" and any(k.startswith("demo-") for k in self.auth_tokens):
            raise ValueError("Replace demo credentials in AUTH_TOKENS before enabling real providers")
        if self.auth_mode == "oidc":
            from urllib.parse import urlparse
            for value in (self.oidc_issuer, self.oidc_jwks_url):
                url = urlparse(value)
                if url.scheme not in ("http", "https") or not url.netloc:
                    raise ValueError("OIDC requires explicit issuer and JWKS URLs")
            if not self.oidc_audience or not self.oidc_client_id:
                raise ValueError("OIDC audience and SPA client ID must be configured")
        if not self.auth_tokens or any(not k or not v for k,v in self.auth_tokens.items()):
            raise ValueError("Configure at least one nonempty token and group")
        if self.provider == "openai-compatible" and not self.api_key.get_secret_value():
            raise ValueError("API_KEY is required for openai-compatible")
        return self
    @property
    def namespace(self):
        return ("demo-hash-v1" if self.provider == "demo" else f"{self.provider}:{self.embedding_model}") + ":acl-v2"
