import sys
import json
from pathlib import Path
from src.services.graph.workflow import app
from src.utils.input_product import PRODUCT_DATA

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

initial_state = {
    "raw_product_data": PRODUCT_DATA,
    "product": None,
    "questions": None,
    "faq_page": None,
    "product_page": None,
    "comparison_page": None
}

result = app.invoke(initial_state)

# Create output directory
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Save JSON files
faq_json = json.dumps(result["faq_page"], indent=2, ensure_ascii=False)
product_json = json.dumps(result["product_page"], indent=2, ensure_ascii=False)
comparison_json = json.dumps(result["comparison_page"], indent=2, ensure_ascii=False)

# Write to files
(output_dir / "faq.json").write_text(faq_json, encoding='utf-8')
(output_dir / "product_page.json").write_text(product_json, encoding='utf-8')
(output_dir / "comparison_page.json").write_text(comparison_json, encoding='utf-8')

print("\nContent generation completed successfully!")
print(f"JSON files saved to '{output_dir}' directory\n")

# Pretty print the JSON results
print("="*50)
print("FAQ PAGE")
print("="*50)
print(faq_json)

print("\n" + "="*50)
print("PRODUCT PAGE")
print("="*50)
print(product_json)

print("\n" + "="*50)
print("COMPARISON PAGE")
print("="*50)
print(comparison_json)
