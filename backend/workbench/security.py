import hashlib
import secrets
from dataclasses import dataclass
from fastapi import HTTPException

@dataclass(frozen=True)
class Principal:
    subject: str
    groups: tuple[str, ...]

def authenticate(token: str, configured: dict[str, list[str]]) -> Principal:
    for known, groups in configured.items():
        if secrets.compare_digest(token, known):
            return Principal(hashlib.sha256(token.encode()).hexdigest()[:12], tuple(groups))
    raise HTTPException(status_code=401, detail="Credencial inválida")

def require_operations(principal: Principal):
    if "operations" not in principal.groups:
        raise HTTPException(status_code=403, detail="Acesso restrito a operations")
