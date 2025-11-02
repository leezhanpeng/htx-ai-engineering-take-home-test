from mcp.types import Tool, TextContent
from dateutil import parser

date_normaliser_definition = Tool(
    name="normalise_date",
    description="Normalise date strings like '21 March 2021' or '4 December 2002' to ISO format (YYYY-MM-DD)",
    inputSchema={
        "type": "object",
        "properties": {
            "date_string": {
                "type": "string",
                "description": "The date string to normalise (e.g., '21 March 2021')"
            }
        },
        "required": ["date_string"]
    }
)

def date_normaliser_executable(arguments):
    date_string = arguments.get("date_string", "")
    try:
        parsed_date = parser.parse(date_string)
        normalized = parsed_date.strftime("%Y-%m-%d")
        return [TextContent(type="text", text=normalized)]
    except Exception as e:
        error_msg = f"Error: Could not parse date '{date_string}'. {str(e)}"
        return [TextContent(type="text", text=error_msg)]
    
date_normaliser = {"definition": date_normaliser_definition, "executable": date_normaliser_executable}
