from src.services.agents.base import BaseAgent
from src.services.tools.benefits_tool import BenefitsTool
from src.services.tools.usage_tool import UsageTool
from src.services.tools.comparision_tool import ComparisonTool
from src.services.llm_service import get_llm_service
import json


class PageGenerationAgent(BaseAgent):
    name = "page-generation-agent"

    def __init__(self):
        self.llm = get_llm_service()
        self.benefits_tool = BenefitsTool()
        self.usage_tool = UsageTool()
        self.comparison_tool = ComparisonTool()

    def run(self, state):
        product = state["product"]
        questions = state.get("questions", {})

        # Generate FAQ page using LLM
        faq_page = self._generate_faq_page(product, questions)
        
        # Generate Product page using content logic blocks (tools)
        product_page = self._generate_product_page(product)
        
        # Generate Comparison page
        comparison_page = self._generate_comparison_page(product)

        return {
            "faq_page": faq_page,
            "product_page": product_page,
            "comparison_page": comparison_page
        }
    
    def _generate_faq_page(self, product, questions):
        """Generate FAQ page with answers using LLM."""
        
        # Extract at least 5 questions from different categories
        selected_questions = []
        for category, q_list in questions.items():
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
            print(f"Generated FAQ page with {len(faq_page.get('items', []))} Q&As")
            return faq_page
        except Exception as e:
            print(f"Warning: FAQ generation failed: {e}")
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
        
        print("Generating product page with content logic blocks...")
        
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
        
        print(f"Product page generated for {product['name']}")
        return product_page
    
    def _generate_comparison_page(self, product):
        """Generate comparison page with a fictional competitor."""
        
        # Create a fictional competitor product
        fictional_product = {
            "name": "RadiantFix Vitamin C Serum",
            "ingredients": ["Vitamin C", "Niacinamide", "Vitamin E"],
            "benefits": ["Brightening", "Oil control", "Antioxidant protection"],
            "price": 899
        }
        
        print("Generating comparison page...")
        comparison_page = self.comparison_tool(product, fictional_product)
        print(f"Comparison page generated")
        
        return comparison_page
