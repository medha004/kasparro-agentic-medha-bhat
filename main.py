import sys
import json
from pathlib import Path
from src.services.graph.workflow import app, visualize_workflow
from src.utils.input_product import PRODUCT_DATA

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')



# Visualize the workflow structure
visualize_workflow()

# Initialize state with proper fields for multi-agent coordination
initial_state = {
    "raw_product_data": PRODUCT_DATA,
    "product": None,
    "questions": None,
    "faq_page": None,
    "product_page": None,
    "comparison_page": None,
    "plan": [],
    "messages": [],
    "active_agents": [],
    "completed_tasks": [],
    "iteration_count": 0,
    "needs_refinement": None,
    "orchestrator_reasoning": "",
    "next_agent": None
}


# Run the multi-agent workflow
result = app.invoke(initial_state)



# Create output directory
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Save JSON files
faq_json = json.dumps(result.get("faq_page", {}), indent=2, ensure_ascii=False)
product_json = json.dumps(result.get("product_page", {}), indent=2, ensure_ascii=False)
comparison_json = json.dumps(result.get("comparison_page", {}), indent=2, ensure_ascii=False)

# Write to files
(output_dir / "faq.json").write_text(faq_json, encoding='utf-8')
(output_dir / "product_page.json").write_text(product_json, encoding='utf-8')
(output_dir / "comparison_page.json").write_text(comparison_json, encoding='utf-8')



