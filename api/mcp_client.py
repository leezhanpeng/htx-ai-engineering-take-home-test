import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

class MCPClient:
    def __init__(self, server_script_path: str):
        self.server_script_path = os.path.abspath(server_script_path)
        self.exit_stack = AsyncExitStack()
        self.session = None

    async def connect(self):
        server_params = StdioServerParameters(
            command=sys.executable,  # Use same Python interpreter so subprocess can import mcp
            args=[self.server_script_path]
        )
        
        streams = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = streams
        
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        
        await self.session.initialize()
        
    async def list_tools(self):
        if not self.session:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        response = await self.session.list_tools()
        return response.tools
    
    async def call_tool(self, tool_name: str, arguments: dict):
        if not self.session:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        result = await self.session.call_tool(tool_name, arguments)
        return result.content[0].text
    
    async def close(self):
        await self.exit_stack.aclose()
