"""Identity is verified first; roles grant permissions, never tool arguments."""
import hashlib
import secrets
from dataclasses import dataclass
import jwt
from fastapi import HTTPException
from .config import Settings

ROLE_PERMISSIONS = {
    "knowledge-manager": {"documents:search", "documents:write"},
    "query-l1": {"documents:search"},
    "query-l2": {"documents:search", "metrics:read", "ai-metrics:read"},
}
ROLE_LABELS = {"knowledge-manager":"Gestor de conhecimento", "query-l1":"Consulta nível 1", "query-l2":"Consulta nível 2"}

@dataclass(frozen=True)
class Principal:
    subject: str
    groups: tuple[str, ...]
    roles: tuple[str, ...]
    permissions: frozenset[str]
    name: str

def from_roles(subject, roles, name=""):
    roles = tuple(sorted(set(roles).intersection(ROLE_PERMISSIONS)))
    if not roles:
        raise HTTPException(status_code=403, detail="Usuário sem perfil autorizado")
    permissions = frozenset(p for role in roles for p in ROLE_PERMISSIONS[role])
    groups = ("level1","level2") if set(roles).intersection({"knowledge-manager","query-l2"}) else ("level1",)
    return Principal(subject,groups,roles,permissions,name or subject)

class Authenticator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.jwks = jwt.PyJWKClient(settings.oidc_jwks_url,timeout=5) if settings.auth_mode == "oidc" else None

    def authenticate(self, token: str) -> Principal:
        if self.settings.auth_mode == "demo":
            for known, roles in self.settings.auth_tokens.items():
                if secrets.compare_digest(token,known):
                    # Compatibility for v0.1 .env; operations is now read-level 2, not an editor.
                    if "operations" in roles: roles = ["query-l2"]
                    elif "employees" in roles: roles = ["query-l1"]
                    return from_roles(hashlib.sha256(token.encode()).hexdigest()[:12], roles, "Usuário demo")
            raise HTTPException(status_code=401,detail="Credencial inválida")
        try:
            key = self.jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(token,key,algorithms=["RS256"],audience=self.settings.oidc_audience,
                                issuer=self.settings.oidc_issuer,
                                options={"require":["exp","iat","sub","iss","aud"]})
        except (jwt.PyJWTError, ValueError, TypeError, KeyError):
            raise HTTPException(status_code=401,detail="Access token inválido ou expirado") from None
        roles = claims
        for part in self.settings.oidc_roles_claim.split("."):
            roles = roles.get(part,{}) if isinstance(roles,dict) else {}
        if not isinstance(roles,list) or any(not isinstance(role,str) for role in roles):
            roles=[]
        return from_roles(claims["sub"], roles, claims.get("preferred_username",claims["sub"]))

def require(principal: Principal, permission: str):
    if permission not in principal.permissions:
        raise HTTPException(status_code=403,detail=f"Permissão necessária: {permission}")

def authorize_tool(principal: Principal, tool: str, service: str | None = None):
    permissions = {"search_documents":"documents:search", "get_service_metrics":"metrics:read", "get_ai_quality_metrics":"ai-metrics:read"}
    if tool not in permissions:
        raise HTTPException(status_code=403,detail="Ferramenta não autorizada")
    require(principal,permissions[tool])
    if tool == "get_service_metrics" and service not in ("orders-api","payments-api"):
        raise HTTPException(status_code=403,detail="Serviço fora do escopo permitido")
