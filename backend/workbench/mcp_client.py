import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .config import Settings

async def call_tool(settings: Settings, token: str, tool: str, arguments: dict, snapshot=None):
    if tool not in ("get_service_metrics","get_ai_quality_metrics"):
        raise ValueError("Tool not allowed")
    # Trusted same-application stdio worker; no remote token passthrough.
    # Only identity settings cross this process boundary, never API keys or database credentials.
    data=settings.model_dump()
    data={k:v for k,v in data.items() if k.startswith("oidc_") or k in ("auth_mode","auth_tokens")}
    env={k.upper():json.dumps(v) if isinstance(v,dict) else str(v) for k,v in data.items()}
    env["MCP_AUTH_TOKEN"]=token
    if snapshot is not None: env["MCP_AI_SNAPSHOT"]=json.dumps(snapshot)
    env["PYTHONPATH"]=str(Path(__file__).resolve().parents[1])
    params=StdioServerParameters(command=sys.executable,args=["-m","workbench.mcp_server"],env=env,cwd="/tmp" if sys.platform!="win32" else None)
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            result=await session.call_tool(tool,arguments)
    if result.isError: raise RuntimeError("MCP tool rejected the request")
    for item in result.content:
        if item.type=="text": return json.loads(item.text)
    raise RuntimeError("No MCP result")

async def call_metrics(settings,token,service):
    return await call_tool(settings,token,"get_service_metrics",{"service":service})

async def call_ai_metrics(settings,token,snapshot):
    return await call_tool(settings,token,"get_ai_quality_metrics",{},snapshot)
