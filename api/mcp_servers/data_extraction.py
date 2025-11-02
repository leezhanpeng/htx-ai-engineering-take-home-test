import sys
import os

# Since we are running this MCP server as a subprocess, we need to make sure it is referencing
# and using the same Python environment as the main API process.
# Credits to Claude for this snippet
if __name__ == "__main__":
    api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if api_dir not in sys.path:
        sys.path.insert(0, api_dir)

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Tools to include in the server
from mcp_servers.tools.date_normaliser import date_normaliser

app = Server("Data Extraction MCP Server")

available_tools = [
    date_normaliser
]
tool_mapper = {tool["definition"].name: tool["executable"] for tool in available_tools}

@app.list_tools()
async def list_tools():
    # Used to output tool definition, so executable should not be included
    return [tool["definition"] for tool in available_tools]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name not in tool_mapper:
        raise ValueError(f"Unknown tool: {name}")
    
    tool = tool_mapper[name]
    return tool(arguments)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
