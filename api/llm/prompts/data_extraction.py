from pydantic import BaseModel

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
    if output_type == "str":
        class StrFormat(BaseModel):
            value: str
            reason: str
        return StrFormat
    if output_type == "int":
        class IntFormat(BaseModel):
            value: int
            reason: str
        return IntFormat
    if output_type == "float":
        class FloatFormat(BaseModel):
            value: float
            reason: str
        return FloatFormat
    if output_type == "list[str]":
        class ListStrFormat(BaseModel):
            value: list[str]
            reason: str
        return ListStrFormat
    if output_type == "list[int]":
        class ListIntFormat(BaseModel):
            value: list[int]
            reason: str
        return ListIntFormat
    if output_type == "list[float]":
        class ListFloatFormat(BaseModel):
            value: list[float]
            reason: str
        return ListFloatFormat

    raise ValueError("Output type not part of available option.")
