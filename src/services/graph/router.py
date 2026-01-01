# src/services/graph/router.py
"""
Dynamic routing logic that adapts based on state analysis.
This replaces hard-coded edges with intelligent decision-making.
"""
from src.utils.state import AgentState
from typing import Literal


def analyze_and_route(state: AgentState) -> Literal["orchestrator", "synthesizer", "END"]:
    """
    Dynamically decide the next node based on state analysis.
    This is the key to adaptive, non-linear workflows.
    """
    
    # Check if we've completed synthesis
    if state.get("needs_refinement") is False:
        completed_tasks = state.get("completed_tasks", [])
        if "quality_check" in completed_tasks:
            print("\n[ROUTER] All work complete → END")
            return "END"
    
    # Check if refinement is needed
    if state.get("needs_refinement"):
        iteration = state.get("iteration_count", 0)
        if iteration < 2:
            print(f"\n[ROUTER] Refinement needed (iteration {iteration}) → orchestrator")
            return "orchestrator"
        else:
            print("\n[ROUTER] Max iterations reached → synthesizer")
            return "synthesizer"
    
    # Check what's been completed
    completed_tasks = state.get("completed_tasks", [])
    
    # If nothing completed yet, go to orchestrator to plan
    if not completed_tasks:
        print("\n[ROUTER] Starting workflow → orchestrator")
        return "orchestrator"
    
    # If we have all pages but no quality check, synthesis should happen
    has_all_pages = (
        state.get("faq_page") and 
        state.get("product_page") and 
        state.get("comparison_page")
    )
    
    if has_all_pages and "quality_check" not in completed_tasks:
        print("\n[ROUTER] Content ready → synthesizer")
        return "synthesizer"
    
    # If synthesis done and quality approved, we're done
    if "quality_check" in completed_tasks:
        print("\n[ROUTER] Quality approved → END")
        return "END"
    
    # Default: go to synthesizer to check what's missing
    print("\n[ROUTER] Default routing → synthesizer")
    return "synthesizer"


def should_continue_after_workers(state: AgentState) -> Literal["quality_checker", "synthesizer"]:
    """
    Decide if we should check quality or go straight to synthesis.
    Demonstrates conditional routing based on state.
    """
    
    # Check if we have all the required pages
    has_all_pages = (
        state.get("faq_page") and 
        state.get("product_page") and 
        state.get("comparison_page")
    )
    
    # Check if quality has been checked
    completed_tasks = state.get("completed_tasks", [])
    quality_checked = "quality_check" in completed_tasks
    
    iteration = state.get("iteration_count", 0)
    
    # If all pages exist and quality not checked and not too many iterations
    if has_all_pages and not quality_checked and iteration < 2:
        print("\n[ROUTER] Pages complete → quality_checker")
        return "quality_checker"
    else:
        print("\n[ROUTER] Skipping quality check → synthesizer")
        return "synthesizer"


def route_after_orchestrator(state: AgentState) -> Literal["assign_workers", "synthesizer"]:
    """
    After orchestrator creates plan, decide if we need to dispatch workers.
    """
    plan = state.get("plan", [])
    
    if plan and len(plan) > 0:
        print(f"\n[ROUTER] Plan has {len(plan)} tasks → assign_workers")
        return "assign_workers"
    else:
        print("\n[ROUTER] No tasks planned → synthesizer")
        return "synthesizer"
