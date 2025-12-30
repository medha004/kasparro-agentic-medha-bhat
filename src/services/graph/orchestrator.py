# src/services/graph/orchestrator.py
from src.utils.state import AgentState
from langgraph.types import Send

def orchestrator_node(state: AgentState):
    """
    Decide WHAT needs to be generated.
    The 'product' is already parsed by the time we get here.
    """
    plan = [
        
        {"type": "generate_questions"},
        {"type": "generate_pages"}
    ]
    return {"plan": plan}

def assign_workers(state: AgentState):
    worker_map = {
        "parse_product": "parse_product_worker",
        "generate_questions": "question_gen_worker",
        "generate_pages": "page_gen_worker"
    }
    
    sends = []
    for task in state.get("plan", []):
        task_type = task["type"]
        node_name = worker_map.get(task_type)
        
        if node_name:
            # Include the parsed product in the payload for workers that need it
            sends.append(
                Send(
                    node_name,
                    {
                        "task": task,
                        "raw_product_data": state["raw_product_data"],
                        "product": state.get("product")
                    }
                )
            )
    return sends