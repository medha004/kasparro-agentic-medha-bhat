from src.services.agents.base import BaseAgent
from src.utils.messages import MessageType
from typing import Dict, Any


class ParseProductAgent(BaseAgent):
    """
    Agent responsible for parsing and structuring raw product data.
    Demonstrates agent autonomy by deciding when parsing is needed.
    """
    name = "parse_product_worker"
    capabilities = ["parse_product", "data_transformation"]
    
    def __init__(self):
        super().__init__()

    def should_activate(self, state: Dict[str, Any]) -> bool:
        """
        Agent decides if it should run based on state.
        Runs if: product data doesn't exist OR raw data changed.
        """
        # Check if product is already parsed
        if not state.get("product"):
            print(f"[{self.name}] Activating: Product not yet parsed")
            return True
        
        # Check if we're being asked to re-parse
        messages = self.read_messages(state)
        if any(msg.content.get("action") == "reparse" for msg in messages):
            print(f"[{self.name}] Activating: Re-parse requested")
            return True
        
        print(f"[{self.name}] Skipping: Product already parsed")
        return False

    def run(self, state):
        """Parse raw product data into structured format."""
        print(f"\n[{self.name}] Parsing product data...")
        
        raw = state.get("raw_product_data", {})
        
        if not raw:
            # Request data from orchestrator
            return self.send_message(
                to_agent="orchestrator",
                message_type=MessageType.REQUEST,
                content={
                    "error": "No raw product data available",
                    "request": "Please provide product data"
                }
            )

        product = {
            "name": raw.get("Product Name", "Unknown"),
            "concentration": raw.get("Concentration", "N/A"),
            "skin_type": raw.get("Skin Type", "").split(", ") if raw.get("Skin Type") else [],
            "ingredients": raw.get("Key Ingredients", "").split(", ") if raw.get("Key Ingredients") else [],
            "benefits": raw.get("Benefits", "").split(", ") if raw.get("Benefits") else [],
            "usage": raw.get("How to Use", ""),
            "side_effects": raw.get("Side Effects", "").split(", ") if raw.get("Side Effects") else [],
            "price": raw.get("Price", 0),
        }
        
        print(f"[{self.name}] ✓ Successfully parsed product: {product['name']}")
        
        # Notify other agents that product is ready
        notification = self.send_message(
            to_agent="broadcast",
            message_type=MessageType.NOTIFY,
            content={
                "status": "product_parsed",
                "product_name": product["name"],
                "available_data": list(product.keys())
            }
        )
        
        result = {"product": product}
        result["messages"] = notification["messages"]
        result["completed_tasks"] = ["parse_product"]
        
        return result
