# src/services/graph/workflow.py
"""
Dynamic multi-agent workflow with adaptive routing and iterative refinement.
This is a TRUE multi-agent system with:
- Dynamic orchestration via LLM reasoning
- Agent autonomy and self-selection  
- Agent-to-agent communication
- Adaptive routing based on state
- Iterative/cyclical flows for refinement
"""
from langgraph.graph import StateGraph, START, END
from src.utils.state import AgentState
from src.services.graph.orchestrator import orchestrator_node
from src.services.agents.parse_product import ParseProductAgent
from src.services.agents.question_generator import QuestionGenerationAgent
from src.services.agents.page_generation import PageGenerationAgent
from src.services.agents.quality_checker import QualityCheckerAgent
from src.services.agents.synthesizer import SynthesizerAgent


def route_after_orchestrator(state: AgentState):
    """
    Dynamic routing after orchestrator based on what's in the plan.
    This demonstrates adaptive workflow paths.
    """
    plan = state.get("plan", [])
    
    if not plan:
        print("\n[ROUTER] No plan → synthesizer")
        return "synthesizer"
    
    # Check what needs to be done first
    first_task = plan[0]["type"]
    
    if first_task == "parse_product_worker":
        print(f"\n[ROUTER] Plan: {len(plan)} tasks → parse_product_worker")
        return "parse_product"
    elif first_task == "question_gen_worker":
        print(f"\n[ROUTER] Plan: {len(plan)} tasks → question_gen_worker")
        return "questions"
    elif first_task == "page_gen_worker":
        print(f"\n[ROUTER] Plan: {len(plan)} tasks → page_gen_worker")
        return "pages"
    else:
        print(f"\n[ROUTER] Default → parse_product_worker")
        return "parse_product"


def route_after_parse(state: AgentState):
    """Route after parsing - check if questions needed."""
    if not state.get("questions"):
        print("\n[ROUTER] Product parsed → question_gen_worker")
        return "questions"
    print("\n[ROUTER] Questions exist → page_gen_worker")
    return "pages"


def route_after_questions(state: AgentState):
    """Route after questions - go to page generation."""
    print("\n[ROUTER] Questions ready → page_gen_worker")
    return "pages"


def route_after_pages(state: AgentState):
    """Route after pages - go to quality check."""
    print("\n[ROUTER] Pages generated → quality_checker")
    return "quality"


def route_after_quality(state: AgentState):
    """Route after quality check - may loop back or continue."""
    if state.get("needs_refinement"):
        iteration = state.get("iteration_count", 0)
        if iteration < 2:
            print(f"\n[ROUTER] Quality issues (iter {iteration}) → orchestrator (CYCLICAL)")
            return "orchestrator"
    
    print("\n[ROUTER] Quality OK → synthesizer")
    return "synthesizer"


def route_after_synthesis(state: AgentState):
    """Route after synthesis - check if we're done."""
    needs_refinement = state.get("needs_refinement")
    
    if needs_refinement is False:
        print("\n[ROUTER] Synthesis complete → END")
        return "END"
    elif needs_refinement:
        iteration = state.get("iteration_count", 0)
        if iteration < 2:
            print(f"\n[ROUTER] More work needed (iter {iteration}) → orchestrator (CYCLICAL)")
            return "orchestrator"
    
    print("\n[ROUTER] Workflow complete → END")
    return "END"


# Initialize the state graph
builder = StateGraph(AgentState)

# Define all agent nodes
builder.add_node("orchestrator", orchestrator_node)
builder.add_node("parse_product_worker", ParseProductAgent())
builder.add_node("question_gen_worker", QuestionGenerationAgent())
builder.add_node("page_gen_worker", PageGenerationAgent())
builder.add_node("quality_checker", QualityCheckerAgent())
builder.add_node("synthesizer", SynthesizerAgent())


# === DYNAMIC WORKFLOW WITH ADAPTIVE ROUTING ===

# 1. Start → Orchestrator (always analyze first)
builder.add_edge(START, "orchestrator")

# 2. Orchestrator → Dynamic routing based on plan
builder.add_conditional_edges(
    "orchestrator",
    route_after_orchestrator,
    {
        "parse_product": "parse_product_worker",
        "questions": "question_gen_worker",
        "pages": "page_gen_worker",
        "synthesizer": "synthesizer"
    }
)

# 3. Parse → Questions or Pages (based on state)
builder.add_conditional_edges(
    "parse_product_worker",
    route_after_parse,
    {
        "questions": "question_gen_worker",
        "pages": "page_gen_worker"
    }
)

# 4. Questions → Pages
builder.add_conditional_edges(
    "question_gen_worker",
    route_after_questions,
    {
        "pages": "page_gen_worker"
    }
)

# 5. Pages → Quality Check
builder.add_conditional_edges(
    "page_gen_worker",
    route_after_pages,
    {
        "quality": "quality_checker"
    }
)

# 6. Quality → Orchestrator (refinement) or Synthesizer
builder.add_conditional_edges(
    "quality_checker",
    route_after_quality,
    {
        "orchestrator": "orchestrator",  # CYCLICAL FLOW
        "synthesizer": "synthesizer"
    }
)

# 7. Synthesizer → Orchestrator (more work) or END
builder.add_conditional_edges(
    "synthesizer",
    route_after_synthesis,
    {
        "orchestrator": "orchestrator",  # CYCLICAL FLOW
        "END": END
    }
)


# Compile the workflow graph
app = builder.compile()




