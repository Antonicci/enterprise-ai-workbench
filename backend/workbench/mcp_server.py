"""Local stdio MCP server; trusted host supplies credentials, never tool arguments."""
import os
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP
from .config import Settings
from .security import authenticate, require_operations
from .retrieval import Retrieval
from .seed import seed

mcp = FastMCP("Enterprise AI Workbench — synthetic operations")

def principal():
    return authenticate(os.environ.get("MCP_AUTH_TOKEN", ""), Settings().auth_tokens)

@mcp.tool()
def get_service_metrics(service: str) -> dict:
    """Read synthetic service metrics. Restricted to operations. No live monitoring."""
    require_operations(principal())
    if service not in ("orders-api","payments-api"):
        raise ValueError("Unknown service")
    return {"service":service,"synthetic":True,"observed_at":datetime.now(timezone.utc).isoformat(),
            "error_rate_pct":4.8 if service == "orders-api" else 0.3,
            "latency_p95_ms":1450 if service == "orders-api" else 320,
            "window_minutes":5}

@mcp.tool()
def search_documents(query: str) -> list[dict]:
    """Search authorized lab documents. Identity comes from host environment."""
    user = principal()
    if not 3 <= len(query) <= 2000:
        raise ValueError("Query must have 3–2000 characters")
    retrieval = Retrieval(Settings())
    seed(retrieval)
    return [c.model_dump() for c in retrieval.search(query,user.groups)]

if __name__ == "__main__":
    mcp.run(transport="stdio")
