# src/services/graph/workflow.py
from langgraph.graph import StateGraph, START, END
from src.utils.state import AgentState
from src.services.graph.orchestrator import orchestrator_node, assign_workers
from src.services.agents.parse_product import ParseProductAgent
from src.services.agents.question_generator import QuestionGenerationAgent
from src.services.agents.page_generation import PageGenerationAgent
from src.services.agents.synthesizer import SynthesizerAgent

builder = StateGraph(AgentState)

# Define Nodes
builder.add_node("orchestrator", orchestrator_node)
builder.add_node("parse_product_worker", ParseProductAgent())
builder.add_node("question_gen_worker", QuestionGenerationAgent())
builder.add_node("page_gen_worker", PageGenerationAgent())
builder.add_node("synthesizer", SynthesizerAgent())

# --- UPDATED EDGES ---

# 1. Start by parsing the product (ensures state["product"] exists)
builder.add_edge(START, "parse_product_worker")

# 2. Once parsed, go to orchestrator to plan the rest
builder.add_edge("parse_product_worker", "orchestrator")

# 3. Orchestrator conditionally sends to content generators
builder.add_conditional_edges(
    "orchestrator",
    assign_workers,
    ["question_gen_worker", "page_gen_worker"],
)

# 4. Workers send output to synthesizer
builder.add_edge("question_gen_worker", "synthesizer")
builder.add_edge("page_gen_worker", "synthesizer")

# 5. Synthesizer ends the workflow
builder.add_edge("synthesizer", END)

app = builder.compile()