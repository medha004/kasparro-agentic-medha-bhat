# src/utils/state.py
from typing_extensions import TypedDict
from typing import List, Dict, Any, Optional
from typing_extensions import Annotated
import operator

class AgentState(TypedDict, total=False):
    """
    State shared across all agents in the workflow.
    This is the single source of truth for the multi-agent system.
    """
    # Input data
    raw_product_data: Dict[str, Any]
    
    # Parsed and processed data
    product: Dict[str, Any]
    questions: Dict[str, Any]
    faq_page: Dict[str, Any]
    product_page: Dict[str, Any]
    comparison_page: Dict[str, Any]

    # Multi-agent coordination
    plan: List[Dict[str, Any]]  # Dynamic plan created by orchestrator
    messages: Annotated[List[Dict[str, Any]], operator.add]  # Agent messages
    active_agents: List[str]  # Currently active agents
    completed_tasks: Annotated[List[str], operator.add]  # Completed task IDs
    
    # Workflow control
    iteration_count: int  # Track iterations for cyclical flows
    needs_refinement: bool  # Flag if content needs refinement
    orchestrator_reasoning: str  # Reasoning behind the plan
    next_agent: Optional[str]  # Dynamically determined next agent