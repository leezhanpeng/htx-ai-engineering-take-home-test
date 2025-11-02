from langgraph.graph import StateGraph, END
from llm.graphs.state import AgentState
from llm.agents.supervisor import Supervisor
from llm.agents.revenue_agent import RevenueAgent
from llm.agents.expenditure_agent import ExpenditureAgent


class MultiAgentGraph:
    def __init__(self, model="gemini-2.0-flash"):
        self.supervisor = Supervisor(model=model)
        self.revenue_agent = RevenueAgent(model=model)
        self.expenditure_agent = ExpenditureAgent(model=model)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("supervisor_route", self._supervisor_route_node)
        workflow.add_node("revenue_agent", self._revenue_agent_node)
        workflow.add_node("expenditure_agent", self._expenditure_agent_node)
        workflow.add_node("supervisor_synthesise", self._supervisor_synthesise_node)

        workflow.set_entry_point("supervisor_route")

        workflow.add_conditional_edges(
            "supervisor_route",
            self._route_to_agents,
            {
                "revenue_only": "revenue_agent",
                "expenditure_only": "expenditure_agent",
                "both": "revenue_agent"
            }
        )

        workflow.add_conditional_edges(
            "revenue_agent",
            self._after_revenue_routing,
            {
                "expenditure": "expenditure_agent",
                "synthesise": "supervisor_synthesise"
            }
        )

        workflow.add_edge("expenditure_agent", "supervisor_synthesise")
        workflow.add_edge("supervisor_synthesise", END)

        return workflow.compile()

    def _supervisor_route_node(self, state):
        decision = self.supervisor.route_query(state["query"])
        return {"supervisor_decision": decision["query_type"]}

    def _revenue_agent_node(self, state):
        findings = self.revenue_agent.analyse(
            query=state["query"],
            pdf_text=state["pdf_text"]
        )
        return {"revenue_findings": findings}

    def _expenditure_agent_node(self, state):
        findings = self.expenditure_agent.analyse(
            query=state["query"],
            pdf_text=state["pdf_text"]
        )
        return {"expenditure_findings": findings}

    def _supervisor_synthesise_node(self, state):
        final_answer = self.supervisor.synthesise_response(
            query=state["query"],
            revenue_findings=state.get("revenue_findings"),
            expenditure_findings=state.get("expenditure_findings")
        )
        return {"final_answer": final_answer}

    def _route_to_agents(self, state):
        decision = state["supervisor_decision"]
        if "revenue_only" in decision:
            return "revenue_only"
        elif "expenditure_only" in decision:
            return "expenditure_only"
        else:
            return "both"

    def _after_revenue_routing(self, state):
        decision = state["supervisor_decision"]
        if "combined" in decision or "both" in decision:
            return "expenditure"
        else:
            return "synthesise"

    async def run(self, query, pdf_text):
        initial_state = {
            "query": query,
            "pdf_text": pdf_text,
            "revenue_findings": None,
            "expenditure_findings": None,
            "supervisor_decision": "",
            "final_answer": ""
        }

        accumulated_state = initial_state.copy()

        async for event in self.graph.astream(initial_state):
            for node_name, node_output in event.items():
                accumulated_state.update(node_output)

                if node_name == "supervisor_route":
                    yield {"type": "routing", "decision": accumulated_state["supervisor_decision"]}

                elif node_name == "revenue_agent":
                    findings = node_output.get("revenue_findings", {})
                    yield {
                        "type": "revenue_analysis",
                        "findings": findings,
                        "num_streams": len(findings.get("revenue_streams", [])),
                        "confidence_level": findings.get("confidence_level"),
                        "confidence_explanation": findings.get("confidence_explanation")
                    }

                elif node_name == "expenditure_agent":
                    findings = node_output.get("expenditure_findings", {})
                    yield {
                        "type": "expenditure_analysis",
                        "findings": findings,
                        "num_items": len(findings.get("expenditure_items", [])),
                        "confidence_level": findings.get("confidence_level"),
                        "confidence_explanation": findings.get("confidence_explanation")
                    }

                elif node_name == "supervisor_synthesise":
                    yield {"type": "synthesis"}
                    yield {
                        "type": "final_result",
                        "final_answer": node_output.get("final_answer", ""),
                        "revenue_findings": accumulated_state.get("revenue_findings"),
                        "expenditure_findings": accumulated_state.get("expenditure_findings")
                    }
