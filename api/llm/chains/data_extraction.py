from llm.prompts.data_extraction import DATA_EXTRACTION_SYSTEM_MESSAGE, DATA_EXTRACTION_USER_MESSAGE
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import create_model
from dotenv import load_dotenv
import os

load_dotenv()

class DataExtractionChain:
    def __init__(self, model):
        # Use ChatOpenAI so that we can potentially change to other models that are
        # OpenAI compatible, rather than being tied to Gemini only
        self.llm = ChatOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=model,
            temperature=0.0
        )
    
    def create_chain(self, output_type):
        format_class = self._get_format_class(output_type) # Used to ensure correct output structure and type
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", DATA_EXTRACTION_SYSTEM_MESSAGE),
            ("user", DATA_EXTRACTION_USER_MESSAGE)
        ])
        
        # Create chain
        chain = prompt | self.llm.with_structured_output(format_class)
        return chain
    
    def extract(self, request, output_type, text):
        chain = self.create_chain(output_type)
        result = chain.invoke({
            "request": request,
            "output_type": output_type,
            "text": text,
        })
        print(result)
        print('='*80)
        return result
    
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
