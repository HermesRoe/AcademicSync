"""LangGraph wiring.
   parser -> planner -> auditor -> (conflicts and fewer than 3 re-plans) -> planner
                                -> (clean or cap reached) -> review_gate -> END
   After the user approves in the UI the graph is invoked again with user_approved=True: START -> dispatcher."""
from langgraph.graph import END, START, StateGraph

from src.nodes.auditor_node import auditor_node
from src.nodes.dispatcher_node import dispatcher_node
from src.nodes.parser_node import parser_node
from src.nodes.planner_node import planner_node
from src.state import AcademicState


def review_gate(state):
    return {"dispatch_status": "awaiting user approval"}


def build_graph():
    g = StateGraph(AcademicState)
    g.add_node("parser", parser_node)
    g.add_node("planner", planner_node)
    g.add_node("auditor", auditor_node)
    g.add_node("review_gate", review_gate)
    g.add_node("dispatcher", dispatcher_node)

    g.add_conditional_edges(START, lambda s: "dispatcher" if s.get("user_approved") else "parser",
                            {"parser": "parser", "dispatcher": "dispatcher"})
    g.add_edge("parser", "planner")
    g.add_edge("planner", "auditor")
    g.add_conditional_edges("auditor", lambda s: "planner" if s.get("needs_replan") else "review_gate",
                            {"planner": "planner", "review_gate": "review_gate"})
    g.add_edge("review_gate", END)
    g.add_edge("dispatcher", END)
    return g.compile()
