from typing import Annotated, Literal

from langgraph.graph import StateGraph, END
from chiron_backend.agents.research.state import AgentState
from chiron_backend.agents.research.nodes import (
    pimo_generator_node,
    adversarial_evaluator_node,
    remediation_agent_node,
    qc_router_node,
)

def adversarial_router(state: AgentState) -> Literal["remediation_agent", "qc_router"]:
    adversarial_json = state.get("adversarial_json", {})
    signal = adversarial_json.get("signal", "not_found")
    
    # According to QCRouter config:
    # IF signal == 'not_found' -> novelty confirmed -> qc_router directly
    # IF signal == 'similar_work' or 'exact_match' -> Remediation Agent
    if signal in ["similar_work", "exact_match"]:
        return "remediation_agent"
    
    return "qc_router"

def build_graph():
    # 1. Initialize StateGraph
    workflow = StateGraph(AgentState)

    # 2. Add nodes
    workflow.add_node("pimo_generator", pimo_generator_node)
    workflow.add_node("adversarial_evaluator", adversarial_evaluator_node)
    workflow.add_node("remediation_agent", remediation_agent_node)
    workflow.add_node("qc_router", qc_router_node)

    # 3. Define Entry Point
    workflow.set_entry_point("pimo_generator")

    # 4. Add unconditional edge from PIMO to adversarial
    workflow.add_edge("pimo_generator", "adversarial_evaluator")

    # 5. Add conditional edges based on adversarial output signal
    workflow.add_conditional_edges(
        "adversarial_evaluator",
        adversarial_router,
        {
            "remediation_agent": "remediation_agent",
            "qc_router": "qc_router",
        }
    )

    # 6. Both Remediation and direct success paths converge to QC Router to finalize report
    workflow.add_edge("remediation_agent", "qc_router")
    
    # 7. QC Router goes to END
    workflow.add_edge("qc_router", END)

    # 8. Compile the graph
    app = workflow.compile()
    return app
