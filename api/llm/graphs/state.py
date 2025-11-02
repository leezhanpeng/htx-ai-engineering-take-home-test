from typing import TypedDict


class AgentState(TypedDict):
    query: str
    pdf_text: dict[int, str]
    revenue_findings: dict | None
    expenditure_findings: dict | None
    supervisor_decision: str
    final_answer: str
