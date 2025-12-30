# Content Management System - Agentic Pipeline
Trying out Langgraph's Orchestrator-worker pattern with a mini project where the agentic system generates product content pages given a product data JSON object. This agent uses a multi agent Orchestrator-Worker pattern provided by Langgraph to coordinate specialized workers that handle question generation, page assembly, and content synthesis. 

## Features

 **Parse & Understand Product Data** - Converts raw product data into structured format  
 **Auto-Generate 15+ Categorized Questions** - Creates informational, safety, usage, purchase, and comparison questions  
 **Custom Templates** - FAQ Page, Product Description Page, Comparison Page  
 **Content Logic Blocks** - Reusable tools that transform data into compelling copy  
 **Agent Orchestration** - LangGraph-based workflow with orchestrator and worker agents  
 **JSON Output** - Clean, machine-readable output for all pages  
 **Claude AI Integration** - Uses Claude Sonnet 4.5 for intelligent content generation

## Architecture

```
┌─────────────────┐
│  START          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Parse Product   │ ← Converts raw data to structured model
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Orchestrator    │ ← Plans what content to generate
└────────┬────────┘
         │
         ├──────────────┬─────────────┐
         ▼              ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Question Gen │ │ Page Gen     │ │ ...          │
│ Worker       │ │ Worker       │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
                ┌──────────────┐
                │ Synthesizer  │ ← Combines all outputs
                └──────┬───────┘
                       │
                       ▼
                   ┌───────┐
                   │  END  │
                   └───────┘
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=your_claude_api_key_here
```

Get your API key from: https://console.anthropic.com/

### 3. Run the System

```bash
python -m main
```

## Output

The system generates three JSON files in the `output/` directory:

- **faq.json** - FAQ page with Q&As
- **product_page.json** - Product description page
- **comparison_page.json** - Product comparison page

## Project Structure

```
content_management_system/
├── src/
│   ├── services/
│   │   ├── agents/           # Agent implementations
│   │   │   ├── base.py
│   │   │   ├── parse_product.py
│   │   │   ├── question_generator.py
│   │   │   ├── page_generation.py
│   │   │   └── synthesizer.py
│   │   ├── graph/            # LangGraph workflow
│   │   │   ├── workflow.py
│   │   │   └── orchestrator.py
│   │   ├── tools/            # Content logic blocks
│   │   │   ├── benefits_tool.py
│   │   │   ├── usage_tool.py
│   │   │   └── comparision_tool.py
│   │   └── llm_service.py    # Claude API wrapper
│   └── utils/
│       ├── state.py          # State management
│       └── input_product.py  # Sample product data
├── output/                   # Generated JSON files
├── main.py                   # Entry point
├── requirements.txt
└── .env                      # API keys (not in git)
```

## How It Works

### 1. Product Parsing
Converts raw product data into a clean internal model.

### 2. Question Generation (LLM)
Uses Claude to generate 15+ categorized questions across:
- Informational
- Safety
- Usage
- Purchase
- Comparison

### 3. Content Logic Blocks (Tools)
Reusable functions that transform data:
- **BenefitsTool**: Enhances benefits into compelling copy
- **UsageTool**: Creates detailed step-by-step instructions
- **ComparisonTool**: Generates product comparisons with analysis

### 4. Page Assembly (LLM)
Agents autonomously produce:
- **FAQ Page**: 5+ Q&As with detailed answers
- **Product Page**: Enhanced with marketing copy
- **Comparison Page**: Side-by-side with competitor


## Technologies

- **LangGraph**: Agent orchestration framework
- **Claude Sonnet 4.5**: LLM for content generation
- **Python 3.12+**: Core language
- **Anthropic API**: Claude API integration


