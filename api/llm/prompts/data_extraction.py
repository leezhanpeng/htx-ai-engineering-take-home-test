from pydantic import create_model

DATA_EXTRACTION_SYSTEM_MESSAGE="""You are a data extraction assistant. Your task is to extract specific information from documents with high accuracy.

Guidelines:
- Extract ONLY the requested information
- Be precise and literal with numbers and values
- If the requested information is not found, respond with null
- For lists, extract all items that match the criteria
- Do not infer or calculate values not explicitly stated in the document"""

DATA_EXTRACTION_USER_MESSAGE="""Extract the following information from the provided text:

Request: {prompt}

Expected output type: {output_type}

Document text:
{text}"""


def get_format_class(output_type):
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
        value=(value_type, ...),
        reason=(str, ...)
    )
