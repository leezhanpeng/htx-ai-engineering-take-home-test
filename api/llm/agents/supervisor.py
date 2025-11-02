from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from llm.prompts.agents.supervisor import (
    SUPERVISOR_ROUTING_SYSTEM_MESSAGE,
    SUPERVISOR_ROUTING_USER_MESSAGE,
    SUPERVISOR_SYNTHESIS_SYSTEM_MESSAGE,
    SUPERVISOR_SYNTHESIS_USER_MESSAGE,
)
from pydantic import create_model
import os
from dotenv import load_dotenv
import json

load_dotenv()


class Supervisor:
    def __init__(self, model="gemini-2.0-flash"):
        self.llm = ChatOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=model,
            temperature=0.0
        )

    def _get_routing_output_structure(self):
        return create_model(
            "RoutingDecision",
            agents_to_call=(list[str], ...),
            reasoning=(str, ...),
            query_type=(str, ...)
        )

    def route_query(self, query):
        messages = [
            SystemMessage(content=SUPERVISOR_ROUTING_SYSTEM_MESSAGE),
            HumanMessage(content=SUPERVISOR_ROUTING_USER_MESSAGE.format(query=query))
        ]

        RoutingDecision = self._get_routing_output_structure()
        routing_llm = self.llm.with_structured_output(RoutingDecision)
        result = routing_llm.invoke(messages)

        return {
            "agents_to_call": result.agents_to_call,
            "reasoning": result.reasoning,
            "query_type": result.query_type
        }

    def synthesise_response(self, query, revenue_findings, expenditure_findings):
        revenue_text = "Not analysed" if revenue_findings is None else json.dumps(revenue_findings, indent=2)
        expenditure_text = "Not analysed" if expenditure_findings is None else json.dumps(expenditure_findings, indent=2)

        synthesis_content = SUPERVISOR_SYNTHESIS_USER_MESSAGE.format(
            query=query,
            revenue_findings=revenue_text,
            expenditure_findings=expenditure_text
        )

        messages = [
            SystemMessage(content=SUPERVISOR_SYNTHESIS_SYSTEM_MESSAGE),
            HumanMessage(content=synthesis_content)
        ]

        result = self.llm.invoke(messages)
        return result.content
