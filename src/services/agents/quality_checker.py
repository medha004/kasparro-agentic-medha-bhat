# src/services/agents/quality_checker.py
from src.services.agents.base import BaseAgent
from src.utils.messages import MessageType
from typing import Dict, Any


class QualityCheckerAgent(BaseAgent):
    """
    Quality assurance agent that validates generated content.
    Can request refinement from other agents, demonstrating iterative flows.
    """
    name = "quality_checker"
    capabilities = ["quality_check", "validation", "content_review"]
    
    def __init__(self):
        super().__init__()
        self.max_iterations = 2  # Prevent infinite loops
    
    def should_activate(self, state: Dict[str, Any]) -> bool:
        """
        Activate when content is generated but hasn't been checked yet.
        """
        iteration = state.get("iteration_count", 0)
        
        # Don't run if we've exceeded max iterations
        if iteration >= self.max_iterations:
            print(f"[{self.name}] Skipping: Max iterations reached")
            return False
        
        # Activate if pages exist but haven't been quality checked
        has_pages = (
            state.get("faq_page") and 
            state.get("product_page") and 
            state.get("comparison_page")
        )
        
        # Check if already validated
        completed_tasks = state.get("completed_tasks", [])
        already_checked = "quality_check" in completed_tasks
        
        if has_pages and not already_checked:
            print(f"[{self.name}] Activating: Content ready for quality check")
            return True
        
        print(f"[{self.name}] Skipping: No content to check or already validated")
        return False
    
    def run(self, state):
        """Validate content quality and request refinement if needed."""
        print(f"\n[{self.name}] Checking content quality...")
        
        issues = []
        messages_to_send = []
        
        # Check FAQ page quality
        faq_page = state.get("faq_page", {})
        faq_items = faq_page.get("items", [])
        if len(faq_items) < 4:
            issues.append("FAQ page has too few questions")
            messages_to_send.append({
                "from_agent": self.name,
                "to_agent": "page_gen_worker",
                "message_type": "request",
                "content": {
                    "action": "refine",
                    "target": "faq_page",
                    "reason": "Need at least 4 Q&As"
                },
                "timestamp": "",
                "reply_to": None
            })
        
        # Check product page quality
        product_page = state.get("product_page", {})
        benefits = product_page.get("benefits", [])
        if isinstance(benefits, list) and len(benefits) < 2:
            issues.append("Product page has insufficient benefits")
        
        # Check comparison page quality
        comparison_page = state.get("comparison_page", {})
        if not comparison_page.get("products"):
            issues.append("Comparison page missing product data")
        
        iteration = state.get("iteration_count", 0)
        
        if issues and iteration < self.max_iterations - 1:
            print(f"[{self.name}] ⚠ Quality issues found: {', '.join(issues)}")
            print(f"[{self.name}]   Requesting refinement (iteration {iteration + 1})")
            
            return {
                "needs_refinement": True,
                "iteration_count": iteration + 1,
                "messages": messages_to_send,
                "completed_tasks": []  # Don't mark as complete since refinement needed
            }
        else:
            print(f"[{self.name}] ✓ Content quality acceptable")
            
            return {
                "needs_refinement": False,
                "messages": [{
                    "from_agent": self.name,
                    "to_agent": "broadcast",
                    "message_type": "notify",
                    "content": {
                        "status": "quality_approved",
                        "issues_found": len(issues),
                        "iteration": iteration
                    },
                    "timestamp": "",
                    "reply_to": None
                }],
                "completed_tasks": ["quality_check"]
            }
