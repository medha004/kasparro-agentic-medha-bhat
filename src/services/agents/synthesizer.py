# src/services/agents/synthesizer.py
from src.services.agents.base import BaseAgent
from src.utils.messages import MessageType
from typing import Dict, Any


class SynthesizerAgent(BaseAgent):
    """
    Autonomous agent that synthesizes outputs from all workers.
    Decides when synthesis is complete or if refinement is needed.
    """
    name = "synthesizer"
    capabilities = ["synthesis", "validation", "coordination"]
    
    def __init__(self):
        super().__init__()
    
    def should_activate(self, state: Dict[str, Any]) -> bool:
        """
        Activate when all required data is present.
        """
        # Check if we have all required outputs
        has_product = state.get("product") is not None
        has_questions = state.get("questions") is not None
        has_faq = state.get("faq_page") is not None
        has_product_page = state.get("product_page") is not None
        has_comparison = state.get("comparison_page") is not None
        
        all_complete = has_product and has_questions and has_faq and has_product_page and has_comparison
        
        if all_complete:
            print(f"[{self.name}] Activating: All content ready for synthesis")
            return True
        
        # Check if explicitly requested
        messages = self.read_messages(state)
        if any(msg.message_type == MessageType.REQUEST for msg in messages):
            print(f"[{self.name}] Activating: Synthesis requested")
            return True
        
        print(f"[{self.name}] Skipping: Not all content ready yet")
        return False

    def run(self, state):
        """Synthesize all outputs and validate completeness."""
        print(f"\n[{self.name}] Synthesizing outputs...")
        
        # Gather all outputs
        result = {
            "product": state.get("product"),
            "questions": state.get("questions"),
            "faq_page": state.get("faq_page"),
            "product_page": state.get("product_page"),
            "comparison_page": state.get("comparison_page")
        }
        
        # Validate completeness
        missing = []
        if not result["product"]:
            missing.append("product")
        if not result["questions"]:
            missing.append("questions")
        if not result["faq_page"]:
            missing.append("faq_page")
        if not result["product_page"]:
            missing.append("product_page")
        if not result["comparison_page"]:
            missing.append("comparison_page")
        
        if missing:
            print(f"[{self.name}] Warning: Missing components - {', '.join(missing)}")
            # Request missing components
            messages_to_send = []
            for component in missing:
                if component == "product":
                    messages_to_send.append({
                        "from_agent": self.name,
                        "to_agent": "parse_product_worker",
                        "message_type": "request",
                        "content": {"request": "Product parsing needed"},
                        "timestamp": "",
                        "reply_to": None
                    })
                elif component == "questions":
                    messages_to_send.append({
                        "from_agent": self.name,
                        "to_agent": "question_gen_worker",
                        "message_type": "request",
                        "content": {"request": "Questions generation needed"},
                        "timestamp": "",
                        "reply_to": None
                    })
            
            result["messages"] = messages_to_send
            result["needs_refinement"] = True
        else:
            print(f"[{self.name}] ✓ All content synthesized successfully")
            
            # Send completion notification
            result["messages"] = [{
                "from_agent": self.name,
                "to_agent": "broadcast",
                "message_type": "notify",
                "content": {
                    "status": "synthesis_complete",
                    "components": ["product", "questions", "faq_page", "product_page", "comparison_page"]
                },
                "timestamp": "",
                "reply_to": None
            }]
            result["needs_refinement"] = False
        
        return result
