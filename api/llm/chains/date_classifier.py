from llm.prompts.date_classifier import DATE_CLASSIFIER_SYSTEM_MESSAGE, DATE_CLASSIFIER_USER_MESSAGE
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import create_model
from dotenv import load_dotenv
import os

load_dotenv()

class DateClassifierChain:
    def __init__(self, model):
        # Use ChatOpenAI for OpenAI compatible models
        self.llm = ChatOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=model,
            temperature=0.0
        )

    def classify(self, normalised_date, reference_date="2024-01-01"):
        messages = [
            SystemMessage(content=DATE_CLASSIFIER_SYSTEM_MESSAGE),
            HumanMessage(content=DATE_CLASSIFIER_USER_MESSAGE.format(
                normalised_date=normalised_date,
                reference_date=reference_date
            ))
        ]

        format_class = self._get_format_class()
        llm_with_structure = self.llm.with_structured_output(format_class)
        return llm_with_structure.invoke(messages)

    def _get_format_class(self):
        return create_model(
            "DateClassification",
            normalised_date=(str, ...),
            reference_date=(str, ...),
            reason=(str, ...),
            classification=(str, ...),
        )
