# src/services/agents/synthesizer.py
from src.services.agents.base import BaseAgent

class SynthesizerAgent(BaseAgent):
    name = "synthesizer"

    def run(self, state):
        # Read from the keys populated by the workers
        return {
            "product": state.get("product"),
            "FAQ": state.get("questions"),
            "faq_page": state.get("faq_page"),
            "product_page": state.get("product_page"),
            "comparison_page": state.get("comparison_page")
        }