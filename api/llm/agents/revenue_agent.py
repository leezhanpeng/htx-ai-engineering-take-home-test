from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from llm.prompts.agents.revenue_agent import REVENUE_AGENT_SYSTEM_MESSAGE, REVENUE_AGENT_USER_MESSAGE
from pydantic import create_model, Field
import os
from dotenv import load_dotenv

load_dotenv()


class RevenueAgent:
    def __init__(self, model="gemini-2.0-flash"):
        self.llm = ChatOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=model,
            temperature=0.0
        )

    def _get_revenue_output_structure(self):
        RevenueStreamItem = create_model(
            "RevenueStreamItem",
            category=(str, ...),
            amount=(float | None, None),
            unit=(str | None, None),
            year=(str | None, None),
            page=(int | None, None),
            context=(str | None, None)
        )

        TotalRevenue = create_model(
            "TotalRevenue",
            amount=(float | None, None),
            unit=(str | None, None)
        )

        RevenueFinding = create_model(
            "RevenueFinding",
            revenue_streams=(list[RevenueStreamItem], Field(default_factory=list)),
            total_revenue=(TotalRevenue | None, None),
            key_insights=(list[str], Field(default_factory=list)),
            confidence_level=(str, "medium"),
            confidence_explanation=(str | None, None)
        )

        return RevenueFinding

    async def analyse(self, query, pdf_text):
        combined_text = "\n\n".join([
            f"[Page {page_num}]\n{text}"
            for page_num, text in sorted(pdf_text.items())
        ])

        messages = [
            SystemMessage(content=REVENUE_AGENT_SYSTEM_MESSAGE),
            HumanMessage(content=REVENUE_AGENT_USER_MESSAGE.format(query=query, text=combined_text))
        ]

        RevenueFinding = self._get_revenue_output_structure()
        llm_with_structure = self.llm.with_structured_output(RevenueFinding)
        result = llm_with_structure.invoke(messages)

        return {
            "revenue_streams": [stream.model_dump() for stream in result.revenue_streams],
            "total_revenue": result.total_revenue.model_dump() if result.total_revenue else None,
            "key_insights": result.key_insights,
            "confidence_level": result.confidence_level,
            "confidence_explanation": result.confidence_explanation
        }
