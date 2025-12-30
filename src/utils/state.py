# src/utils/state.py
from typing_extensions import TypedDict
from typing import List, Dict, Any
from typing_extensions import Annotated
import operator

class AgentState(TypedDict, total=False):
    raw_product_data: Dict[str, Any]
    
    # Add these keys to capture worker outputs
    product: Dict[str, Any]
    questions: Dict[str, Any]
    faq_page: Dict[str, Any]
    product_page: Dict[str, Any]
    comparison_page: Dict[str, Any]

    plan: List[Dict[str, Any]]
    completed_blocks: Annotated[List[Dict[str, Any]], operator.add]
    final_pages: Dict[str, Any]