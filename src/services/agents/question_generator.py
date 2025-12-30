from src.services.agents.base import BaseAgent
from src.services.llm_service import get_llm_service
import json


class QuestionGenerationAgent(BaseAgent):
    name = "question-generation-agent"

    def __init__(self):
        self.llm = get_llm_service()

    def run(self, state):
        product = state["product"]

        system_prompt = """You are an expert content strategist specializing in e-commerce product pages.
Your task is to generate user questions that potential customers might ask about a product.

Generate at least 15 questions across these categories:
- Informational: Questions about what the product is, its features, ingredients
- Safety: Questions about side effects, suitability for skin types
- Usage: Questions about how to use, when to apply, application tips
- Purchase: Questions about pricing, value, availability
- Comparison: Questions comparing with other similar products

CRITICAL: Return ONLY raw JSON - no markdown, no code fences, no backticks.

Output format (raw JSON only):
{
  "informational": ["question1", "question2", ...],
  "safety": ["question1", "question2", ...],
  "usage": ["question1", "question2", ...],
  "purchase": ["question1", "question2", ...],
  "comparison": ["question1", "question2", ...]
}

Ensure you have at least 15 questions total across all categories."""

        user_prompt = f"""Generate categorized user questions for this product:

Product Name: {product['name']}
Concentration: {product.get('concentration', 'N/A')}
Skin Type: {', '.join(product['skin_type'])}
Key Ingredients: {', '.join(product['ingredients'])}
Benefits: {', '.join(product['benefits'])}
Usage Instructions: {product['usage']}
Side Effects: {', '.join(product['side_effects'])}
Price: ₹{product['price']}

Generate realistic, specific questions that customers would ask about this product."""

        try:
            response = self.llm.generate(system_prompt, user_prompt, max_tokens=1500)
            # Parse the JSON response
            questions = json.loads(response)
            
            # Validate we have at least 15 questions
            total_questions = sum(len(q_list) for q_list in questions.values())
            print(f"Generated {total_questions} categorized questions")
            
            return {"questions": questions}
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse LLM response as JSON: {e}")
            print(f"Response was: {response[:200]}...")
            # Fallback to basic questions
            return self._generate_fallback_questions(product)
        except Exception as e:
            print(f"Error generating questions: {e}")
            return self._generate_fallback_questions(product)
    
    def _generate_fallback_questions(self, product):
        """Fallback questions if LLM fails."""
        return {
            "questions": {
                "informational": [
                    f"What is {product['name']}?",
                    "What are the key ingredients?",
                    "What does this product do?"
                ],
                "usage": [
                    "How should I use this product?",
                    "When should I apply it?",
                    "How often should I use it?"
                ],
                "safety": [
                    "Are there any side effects?",
                    "Is it suitable for my skin type?",
                    "Can I use it with other products?"
                ],
                "purchase": [
                    "What is the price?",
                    "Where can I buy it?",
                    "Is it worth the price?"
                ],
                "comparison": [
                    "How does this compare to similar products?",
                    "What makes this product unique?"
                ]
            }
        }
