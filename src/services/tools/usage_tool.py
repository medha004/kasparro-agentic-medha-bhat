from src.services.tools.base import BaseTool
from src.services.llm_service import get_llm_service
import json


class UsageTool(BaseTool):
    """
    Content logic block that transforms usage instructions into detailed, user-friendly steps.
    """
    name = "usage-tool"

    def __init__(self):
        self.llm = get_llm_service()

    def execute(self, usage: str):
        """Transform basic usage into detailed step-by-step instructions."""
        
        system_prompt = """You are a skincare expert creating easy-to-follow product usage instructions.
Transform basic usage information into clear, detailed step-by-step instructions.

Rules:
1. Break down into specific, numbered steps
2. Include timing, quantity, and technique details
3. Add helpful tips where relevant
4. Keep language simple and actionable
5. Return ONLY raw JSON array - no markdown, no code fences, no backticks

CRITICAL: Output must be a raw JSON array only.

Example input: "Apply in the morning"
Example output: ["Cleanse your face thoroughly and pat dry", "Apply 2-3 drops to your fingertips", "Gently massage into face and neck using upward motions", "Wait 1-2 minutes for absorption", "Follow with moisturizer and sunscreen"]"""

        user_prompt = f"""Create detailed step-by-step usage instructions from this:

Basic Usage: {usage}

Return a JSON array of detailed steps."""

        try:
            response = self.llm.generate(system_prompt, user_prompt, max_tokens=600)
            detailed_steps = json.loads(response)
            return detailed_steps
        except Exception as e:
            print(f"Warning: UsageTool LLM call failed: {e}")
            # Fallback to basic usage
            return [usage]
