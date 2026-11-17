import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .config import Settings

async def call_metrics(settings: Settings, token: str, service: str):
    # Only a fixed executable/module may be launched; no user-supplied server URL/command.
    env = {k: (v.get_secret_value() if hasattr(v,"get_secret_value") else
               json.dumps(v) if isinstance(v,dict) else str(v))
           for k,v in settings.model_dump().items()}
    env = {k.upper():v for k,v in env.items()}
    env["MCP_AUTH_TOKEN"] = token
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    params = StdioServerParameters(command=sys.executable,args=["-m","workbench.mcp_server"],env=env)
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            result = await session.call_tool("get_service_metrics",{"service":service})
            if result.isError:
                raise RuntimeError("MCP tool rejected the request")
            for item in result.content:
                if item.type == "text":
                    return json.loads(item.text)
    raise RuntimeError("No MCP result")
