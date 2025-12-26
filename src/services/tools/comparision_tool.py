from src.services.tools.base import BaseTool
from src.services.llm_service import get_llm_service
import json


class ComparisonTool(BaseTool):
    """
    Content logic block that creates detailed product comparisons with analysis.
    """
    name = "comparison-tool"

    def __init__(self):
        self.llm = get_llm_service()

    def execute(self, product_a, product_b):
        """Create a detailed comparison between two products."""
        
        system_prompt = """You are a product comparison expert for skincare items.
Create a detailed, objective comparison between two products highlighting key differences.

CRITICAL: Return ONLY raw JSON - no markdown, no code fences, no backticks.

Return structure:
{
  "products": {
    "product_name_1": {
      "ingredients": ["ingredient1", "ingredient2"],
      "benefits": ["benefit1", "benefit2"],
      "price": 699,
      "best_for": "description of ideal customer"
    },
    "product_name_2": {
      "ingredients": ["ingredient1", "ingredient2"],
      "benefits": ["benefit1", "benefit2"],
      "price": 899,
      "best_for": "description of ideal customer"
    }
  },
  "key_differences": [
    "difference point 1",
    "difference point 2",
    "difference point 3"
  ],
  "verdict": "Brief recommendation based on different use cases"
}"""

        user_prompt = f"""Compare these two products:

Product A:
- Name: {product_a['name']}
- Ingredients: {', '.join(product_a['ingredients'])}
- Benefits: {', '.join(product_a['benefits'])}
- Price: ₹{product_a['price']}

Product B:
- Name: {product_b['name']}
- Ingredients: {', '.join(product_b['ingredients'])}
- Benefits: {', '.join(product_b['benefits'])}
- Price: ₹{product_b['price']}

Create a detailed comparison with analysis."""

        try:
            response = self.llm.generate(system_prompt, user_prompt, max_tokens=1200)
            comparison = json.loads(response)
            return comparison
        except Exception as e:
            print(f"Warning: ComparisonTool LLM call failed: {e}")
            # Fallback to basic comparison
            return {
                "comparison": {
                    product_a["name"]: {
                        "ingredients": product_a["ingredients"],
                        "benefits": product_a["benefits"],
                        "price": product_a["price"]
                    },
                    product_b["name"]: {
                        "ingredients": product_b["ingredients"],
                        "benefits": product_b["benefits"],
                        "price": product_b["price"]
                    }
                }
            }
