from llm.prompts.data_extraction import DATA_EXTRACTION_SYSTEM_MESSAGE, DATA_EXTRACTION_USER_MESSAGE
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from pydantic import create_model
from dotenv import load_dotenv
import os

load_dotenv()

class DataExtractionChain:
    def __init__(self, model, mcp_client=None):
        # Use ChatOpenAI so that we can potentially change to other models that are
        # OpenAI compatible, rather than being tied to Gemini only
        self.llm = ChatOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=model,
            temperature=0.0
        )

        self.mcp_client = mcp_client

    async def _get_tools(self):
        if not self.mcp_client:
            return []

        mcp_tools = await self.mcp_client.list_tools()

        # Need to convert to the below definition to fit OpenAI compatibility
        tool_definitions = []
        for tool in mcp_tools:
            tool_definitions.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })

        return tool_definitions

    async def extract(self, request, output_type, text):
        # Build initial messages
        messages = [
            ("system", DATA_EXTRACTION_SYSTEM_MESSAGE),
            ("user", DATA_EXTRACTION_USER_MESSAGE.format(
                request=request,
                output_type=output_type,
                text=text
            ))
        ]

        # If we have MCP server, provide the knowledge to the inference pipeline
        if self.mcp_client:
            messages = await self._execute_with_MCP(messages)

        # Force a structure in the final output so that we can parse the result with specific typecasting
        return await self._extract_with_structure(messages, output_type)

    async def _execute_with_MCP(self, messages):
        tools = await self._get_tools()
        llm_with_tools = self.llm.bind(tools=tools)

        max_iterations = 10
        for _ in range(max_iterations):
            response = llm_with_tools.invoke(messages)

            if not response.tool_calls:
                messages.append(response)
                messages.append(("user", "Please provide your final answer in the required structured format with 'value' and 'reason' fields."))
                return messages

            messages.append(response)

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                tool_result = await self.mcp_client.call_tool(tool_name, tool_args)

                tool_message = ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"]
                )
                messages.append(tool_message)
        return messages

    async def _extract_with_structure(self, messages, output_type):
        format_class = self._get_format_class(output_type)
        llm_with_structure = self.llm.with_structured_output(format_class)
        return llm_with_structure.invoke(messages)

    def _get_format_class(self, output_type):
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "list[str]": list[str],
            "list[int]": list[int],
            "list[float]": list[float],
        }
        
        if output_type not in type_map:
            raise ValueError(f"Output type '{output_type}' not supported.")
        
        value_type = type_map[output_type]
        
        return create_model(
            "Format",
            value=(value_type | None, None),
            reason=(str, ...)
        )
