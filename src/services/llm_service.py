# src/services/llm_service.py
import os
import re
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def strip_markdown_json(text: str) -> str:
    """
    Strip markdown code fences from JSON responses.
    Claude often returns JSON wrapped in ```json ... ```
    """
    # Remove markdown code fences
    text = text.strip()
    
    # Pattern 1: ```json\n{...}\n```
    if text.startswith('```json'):
        text = re.sub(r'^```json\s*\n', '', text)
        text = re.sub(r'\n```\s*$', '', text)
    
    # Pattern 2: ```\n{...}\n```
    elif text.startswith('```'):
        text = re.sub(r'^```\s*\n', '', text)
        text = re.sub(r'\n```\s*$', '', text)
    
    return text.strip()

class LLMService:
    """
    Wrapper service for Claude API calls.
    Handles all LLM interactions with proper prompts.
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please create a .env file with your API key."
            )
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5"  # Claude Sonnet 4.5 model
    
    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
        """
        Generate content using Claude API.
        
        Args:
            system_prompt: System instruction for the model
            user_prompt: User message/query
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response (with markdown code fences stripped)
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            response = message.content[0].text
            # Strip markdown code fences before returning
            return strip_markdown_json(response)
        except Exception as e:
            raise Exception(f"Error calling Claude API: {str(e)}")

# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

