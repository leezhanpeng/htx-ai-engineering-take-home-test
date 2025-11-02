from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from llm.prompts.agents.expenditure_agent import EXPENDITURE_AGENT_SYSTEM_MESSAGE, EXPENDITURE_AGENT_USER_MESSAGE
from pydantic import create_model, Field
import os
from dotenv import load_dotenv

load_dotenv()


class ExpenditureAgent:
    def __init__(self, model="gemini-2.0-flash"):
        self.llm = ChatOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=model,
            temperature=0.0
        )

    def _get_expenditure_output_structure(self):
        ExpenditureItem = create_model(
            "ExpenditureItem",
            category=(str, ...),
            amount=(float | None, None),
            unit=(str | None, None),
            year=(str | None, None),
            type=(str | None, None),
            page=(int | None, None),
            purpose=(str | None, None),
            funding_source=(str | None, None)
        )

        TotalExpenditure = create_model(
            "TotalExpenditure",
            amount=(float | None, None),
            unit=(str | None, None)
        )

        ExpenditureFinding = create_model(
            "ExpenditureFinding",
            expenditure_items=(list[ExpenditureItem], Field(default_factory=list)),
            total_expenditure=(TotalExpenditure | None, None),
            key_insights=(list[str], Field(default_factory=list)),
            confidence_level=(str, "medium"),
            confidence_explanation=(str | None, None)
        )

        return ExpenditureFinding

    async def analyse(self, query, pdf_text):
        combined_text = "\n\n".join([
            f"[Page {page_num}]\n{text}"
            for page_num, text in sorted(pdf_text.items())
        ])

        messages = [
            SystemMessage(content=EXPENDITURE_AGENT_SYSTEM_MESSAGE),
            HumanMessage(content=EXPENDITURE_AGENT_USER_MESSAGE.format(query=query, text=combined_text))
        ]

        ExpenditureFinding = self._get_expenditure_output_structure()
        llm_with_structure = self.llm.with_structured_output(ExpenditureFinding)
        result = llm_with_structure.invoke(messages)

        return {
            "expenditure_items": [item.model_dump() for item in result.expenditure_items],
            "total_expenditure": result.total_expenditure.model_dump() if result.total_expenditure else None,
            "key_insights": result.key_insights,
            "confidence_level": result.confidence_level,
            "confidence_explanation": result.confidence_explanation
        }
