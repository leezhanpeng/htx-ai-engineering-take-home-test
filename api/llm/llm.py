import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

class LLM:
    def __init__(self, model, temperature=0.0, max_output_tokens=2048):
        self.model_name = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def generate(self, messages):
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
        )
        return response.choices[0].message

    def stream(self, messages):
        stream = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
