from src.services.agents.base import BaseAgent
from src.services.tools.benefits_tool import BenefitsTool
from src.services.tools.usage_tool import UsageTool
from src.services.tools.comparision_tool import ComparisonTool
from src.services.llm_service import get_llm_service
from src.utils.messages import MessageType
from typing import Dict, Any
import json


class PageGenerationAgent(BaseAgent):
    """
    Autonomous agent that generates FAQ, product, and comparison pages.
    Demonstrates modular agent with tool usage and coordination.
    """
    name = "page_gen_worker"
    capabilities = ["generate_pages", "content_creation", "faq", "product_page", "comparison"]

    def __init__(self):
        super().__init__()
        self.llm = get_llm_service()
        self.benefits_tool = BenefitsTool()
        self.usage_tool = UsageTool()
        self.comparison_tool = ComparisonTool()
    
    def should_activate(self, state: Dict[str, Any]) -> bool:
        """
        Activate if any pages are missing or refinement is requested.
        """
        # Check if any pages are missing
        has_faq = state.get("faq_page") is not None
        has_product = state.get("product_page") is not None
        has_comparison = state.get("comparison_page") is not None
        
        if not (has_faq and has_product and has_comparison):
            print(f"[{self.name}] Activating: Pages missing (FAQ: {has_faq}, Product: {has_product}, Comparison: {has_comparison})")
            return True
        
        # Check for refinement requests
        messages = self.read_messages(state)
        for msg in messages:
            if msg.message_type == MessageType.REQUEST:
                if msg.content.get("action") == "refine" and msg.content.get("target") in ["faq_page", "product_page", "comparison_page"]:
                    print(f"[{self.name}] Activating: Refinement requested by {msg.from_agent}")
                    return True
        
        print(f"[{self.name}] Skipping: All pages already generated")
        return False

    def run(self, state):
        """Generate all content pages."""
        print(f"\n[{self.name}] Starting page generation...")
        
        product = state.get("product")
        questions = state.get("questions", {})
        
        if not product:
            # Request product data
            return self.send_message(
                to_agent="parse_product_worker",
                message_type=MessageType.REQUEST,
                content={"action": "parse", "reason": "Need product data for pages"}
            )
        
        if not questions:
            # Request questions
            return self.send_message(
                to_agent="question_gen_worker",
                message_type=MessageType.REQUEST,
                content={"action": "generate", "reason": "Need questions for FAQ"}
            )
        
        result = {}
        
        # Generate FAQ page if missing
        if not state.get("faq_page"):
            result["faq_page"] = self._generate_faq_page(product, questions)
        
        # Generate Product page if missing
        if not state.get("product_page"):
            result["product_page"] = self._generate_product_page(product)
        
        # Generate Comparison page if missing
        if not state.get("comparison_page"):
            result["comparison_page"] = self._generate_comparison_page(product)
        
        # Notify completion
        notification = self.send_message(
            to_agent="broadcast",
            message_type=MessageType.NOTIFY,
            content={
                "status": "pages_generated",
                "pages": list(result.keys())
            }
        )
        
        result["messages"] = notification["messages"]
        result["completed_tasks"] = ["generate_pages"]
        
        print(f"[{self.name}] ✓ Generated {len(result) - 2} pages")  # -2 for messages and completed_tasks
        return result
    
    def _generate_faq_page(self, product, questions):
        """Generate FAQ page with answers using LLM."""
        print(f"[{self.name}]   → Generating FAQ page...")
        
        # Extract at least 5 questions from different categories
        selected_questions = []
        for q_list in questions.values():
            selected_questions.extend(q_list[:2])  # Take 2 from each category
        
        # Limit to reasonable number
        selected_questions = selected_questions[:8]
        
        system_prompt = """You are a customer service expert creating FAQ answers for skincare products.
Generate helpful, accurate answers to customer questions based on product information.

Rules:
1. Answers should be clear, concise, and customer-friendly
2. Base answers on the provided product information
3. Be honest about limitations or side effects
4. Use a professional but warm tone
5. Return ONLY raw JSON - no markdown, no code fences, no backticks

CRITICAL: Output must be raw JSON only.

Return format:
{
  "page": "FAQ",
  "items": [
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."}
  ]
}"""

        user_prompt = f"""Create FAQ answers for these questions about the product:

Product Information:
- Name: {product['name']}
- Concentration: {product.get('concentration', 'N/A')}
- Skin Type: {', '.join(product['skin_type'])}
- Ingredients: {', '.join(product['ingredients'])}
- Benefits: {', '.join(product['benefits'])}
- Usage: {product['usage']}
- Side Effects: {', '.join(product['side_effects'])}
- Price: ₹{product['price']}

Questions to answer:
{json.dumps(selected_questions, indent=2)}

Generate helpful, accurate answers for each question."""

        try:
            response = self.llm.generate(system_prompt, user_prompt, max_tokens=2000)
            faq_page = json.loads(response)
            print(f"[{self.name}]     ✓ FAQ with {len(faq_page.get('items', []))} Q&As")
            return faq_page
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[{self.name}]     ⚠ FAQ generation failed: {e}, using fallback")
            # Fallback FAQ
            return {
                "page": "FAQ",
                "items": [
                    {
                        "question": "What is this product?",
                        "answer": f"{product['name']} is a {product.get('concentration', '')} serum designed for {', '.join(product['skin_type'])} skin."
                    },
                    {
                        "question": "What are the main benefits?",
                        "answer": f"This product offers: {', '.join(product['benefits'])}."
                    },
                    {
                        "question": "How should I use it?",
                        "answer": product['usage']
                    },
                    {
                        "question": "What is the price?",
                        "answer": f"₹{product['price']}"
                    }
                ]
            }
    
    def _generate_product_page(self, product):
        """Generate product page using content logic blocks."""
        print(f"[{self.name}]   → Generating product page...")
        
        # Use tools to transform content
        enhanced_benefits = self.benefits_tool(product["benefits"])
        detailed_usage = self.usage_tool(product["usage"])
        
        product_page = {
            "product_name": product["name"],
            "tagline": f"{product.get('concentration', '')} for {', '.join(product['skin_type'])} skin",
            "ingredients": product["ingredients"],
            "benefits": enhanced_benefits,
            "usage_instructions": detailed_usage,
            "side_effects": product["side_effects"],
            "price": product["price"],
            "skin_type": product["skin_type"]
        }
        
        print(f"[{self.name}]     ✓ Product page for {product['name']}")
        return product_page
    
    def _generate_comparison_page(self, product):
        """Generate comparison page with a fictional competitor."""
        print(f"[{self.name}]   → Generating comparison page...")
        
        # Create a fictional competitor product
        fictional_product = {
            "name": "RadiantFix Vitamin C Serum",
            "ingredients": ["Vitamin C", "Niacinamide", "Vitamin E"],
            "benefits": ["Brightening", "Oil control", "Antioxidant protection"],
            "price": 899
        }
        
        comparison_page = self.comparison_tool(product, fictional_product)
        print(f"[{self.name}]     ✓ Comparison page generated")
        
        return comparison_page
