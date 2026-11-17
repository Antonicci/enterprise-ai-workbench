"""Local stdio MCP server; trusted host supplies credentials, never tool arguments."""
import os
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP
from .config import Settings
from .security import Authenticator, authorize_tool
from .retrieval import Retrieval
from .seed import seed

mcp = FastMCP("Enterprise AI Workbench — synthetic operations")

def principal():
    return Authenticator(Settings()).authenticate(os.environ.get("MCP_AUTH_TOKEN", ""))

@mcp.tool()
def get_service_metrics(service: str) -> dict:
    """Read synthetic service metrics. Restricted to operations. No live monitoring."""
    authorize_tool(principal(),"get_service_metrics",service)
    if service not in ("orders-api","payments-api"):
        raise ValueError("Unknown service")
    return {"source_id":"mcp:get_service_metrics","source_type":"tool_result","service":service,"synthetic":True,"observed_at":datetime.now(timezone.utc).isoformat(),
            "error_rate_pct":4.8 if service == "orders-api" else 0.3,
            "latency_p95_ms":1450 if service == "orders-api" else 320,
            "window_minutes":5}

@mcp.tool()
def search_documents(query: str) -> list[dict]:
    """Search authorized lab documents. Identity comes from host environment."""
    user = principal()
    authorize_tool(user,"search_documents")
    if not 3 <= len(query) <= 2000:
        raise ValueError("Query must have 3–2000 characters")
    retrieval = Retrieval(Settings())
    seed(retrieval)
    return [c.model_dump() for c in retrieval.search(query,user.groups)]

@mcp.tool()
def get_ai_quality_metrics() -> dict:
    """Read measured assistant counters supplied by the trusted host. Quality/tokens may be unmeasured."""
    import json
    authorize_tool(principal(),"get_ai_quality_metrics")
    snapshot=os.environ.get("MCP_AI_SNAPSHOT")
    return json.loads(snapshot) if snapshot else {"available":False,"reason":"No backend snapshot supplied by host"}

if __name__ == "__main__":
    mcp.run(transport="stdio")
