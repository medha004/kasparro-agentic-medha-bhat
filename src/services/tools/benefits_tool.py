from src.services.tools.base import BaseTool
from src.services.llm_service import get_llm_service
from typing import List
import json


class BenefitsTool(BaseTool):
    """
    Content logic block that transforms raw benefits into compelling marketing copy.
    """
    name = "benefits-tool"

    def __init__(self):
        self.llm = get_llm_service()

    def execute(self, benefits: List[str]) -> List[str]:
        """Transform benefits into engaging product descriptions."""
        
        system_prompt = """You are a professional copywriter specializing in skincare product descriptions.
Transform raw product benefits into compelling, customer-focused descriptions.

Rules:
1. Make each benefit customer-centric (focus on "you" not "it")
2. Be specific and actionable
3. Keep each description concise (1-2 sentences)
4. Use professional but approachable tone
5. Return ONLY raw JSON array - no markdown, no code fences, no backticks

CRITICAL: Output must be a raw JSON array only.

Example input: ["Brightening", "Anti-aging"]
Example output: ["Reveals a radiant, even-toned complexion by reducing dullness and dark spots", "Visibly reduces fine lines and wrinkles while improving skin firmness"]"""

        user_prompt = f"""Transform these product benefits into compelling descriptions:

Benefits: {', '.join(benefits)}

Return a JSON array of enhanced benefit descriptions."""

        try:
            response = self.llm.generate(system_prompt, user_prompt, max_tokens=800)
            enhanced_benefits = json.loads(response)
            return enhanced_benefits
        except Exception as e:
            print(f"Warning: BenefitsTool LLM call failed: {e}")
            # Fallback to original benefits
            return benefits
