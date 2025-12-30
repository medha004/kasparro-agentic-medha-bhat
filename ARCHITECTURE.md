# System Architecture

## Overview

This document describes the complete architecture of the LLM-powered Content Management System.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                              │
│                    (Product Data JSON)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH WORKFLOW                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Parse Product Agent                                  │  │
│  │     - Transforms raw data → structured model             │  │
│  │     - No LLM (pure data transformation)                  │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  2. Orchestrator                                         │  │
│  │     - Plans content generation tasks                     │  │
│  │     - Dispatches to worker agents                        │  │
│  └────────┬─────────────────────────────────┬───────────────┘  │
│           │                                 │                   │
│           ▼                                 ▼                   │
│  ┌─────────────────────┐         ┌─────────────────────────┐  │
│  │ 3a. Question Gen    │         │ 3b. Page Gen Agent      │  │
│  │     Worker          │         │     Worker              │  │
│  │                     │         │                         │  │
│  │  🤖 LLM CALL        │         │  ┌──────────────────┐  │  │
│  │  Generate 15+       │         │  │ FAQ Page         │  │  │
│  │  categorized        │         │  │  🤖 LLM CALL     │  │  │
│  │  questions          │         │  │  Answer Qs       │  │  │
│  │                     │         │  └──────────────────┘  │  │
│  │  Categories:        │         │                         │  │
│  │  - Informational    │         │  ┌──────────────────┐  │  │
│  │  - Safety           │         │  │ Product Page     │  │  │
│  │  - Usage            │         │  │                  │  │  │
│  │  - Purchase         │         │  │  🤖 Benefits Tool│  │  │
│  │  - Comparison       │         │  │     (LLM)        │  │  │
│  │                     │         │  │  🤖 Usage Tool   │  │  │
│  └─────────┬───────────┘         │  │     (LLM)        │  │  │
│            │                     │  └──────────────────┘  │  │
│            │                     │                         │  │
│            │                     │  ┌──────────────────┐  │  │
│            │                     │  │ Comparison Page  │  │  │
│            │                     │  │                  │  │  │
│            │                     │  │  🤖 Compare Tool │  │  │
│            │                     │  │     (LLM)        │  │  │
│            │                     │  └──────────────────┘  │  │
│            │                     └──────────┬──────────────┘  │
│            │                                │                  │
│            └────────────┬───────────────────┘                  │
│                         │                                      │
│                         ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  4. Synthesizer Agent                                    │ │
│  │     - Combines all outputs                               │ │
│  │     - Prepares final state                               │ │
│  └────────────────────────┬─────────────────────────────────┘ │
└─────────────────────────────┼────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         OUTPUT                                  │
│                                                                 │
│  output/faq.json              - FAQ with Q&As                  │
│  output/product_page.json     - Enhanced product description   │
│  output/comparison_page.json  - Product comparison             │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Parse Product Agent
**File**: `src/services/agents/parse_product.py`

**Purpose**: Transform raw product data into structured model

**Input**:
```json
{
  "Product Name": "GlowBoost Vitamin C Serum",
  "Concentration": "10% Vitamin C",
  "Skin Type": "Oily, Combination",
  ...
}
```

**Output**:
```json
{
  "name": "GlowBoost Vitamin C Serum",
  "concentration": "10% Vitamin C",
  "skin_type": ["Oily", "Combination"],
  ...
}
```

---

### 2. Orchestrator
**File**: `src/services/graph/orchestrator.py`

**Purpose**: Plan and dispatch tasks to worker agents


**Tasks Created**:
- `generate_questions` → Question Gen Worker
- `generate_pages` → Page Gen Worker

---

### 3a. Question Generation Worker
**File**: `src/services/agents/question_generator.py`

**Purpose**: Generate 15+ categorized user questions

**LLM**: Yes 

**Prompt**:
```
System: Expert content strategist
Task: Generate categorized questions
Output: JSON with 5 categories
```

**API Call**: 1 call, ~1500 tokens

**Output**:
```json
{
  "informational": ["What is...", "How does..."],
  "safety": ["Are there...", "Is it safe..."],
  "usage": ["When should...", "How often..."],
  "purchase": ["What is the price...", "Where to buy..."],
  "comparison": ["How does this compare..."]
}
```

---

### 3b. Page Generation Worker
**File**: `src/services/agents/page_generation.py`

**Purpose**: Generate all three content pages

**LLM**:  Yes (multiple calls through sub-components)

#### Sub-component: FAQ Page Generator

**LLM**:  Yes (Claude Sonnet 4.5)

**Prompt**:
```
System: Customer service expert
Task: Answer FAQ questions
Output: JSON with Q&A pairs
```

**API Call**: 1 call, ~2,000 tokens

**Output**:
```json
{
  "page": "FAQ",
  "items": [
    {"question": "...", "answer": "..."},
    ...
  ]
}
```

#### Sub-component: Product Page Generator

Uses **Content Logic Blocks** (Tools):

##### Benefits Tool
**File**: `src/services/tools/benefits_tool.py`

**LLM**:  Yes (Claude Sonnet 4.5)

**Prompt**:
```
System: Professional copywriter
Task: Transform benefits into engaging copy
Output: JSON array
```

**API Call**: 1 call, ~800 tokens

**Transform**:
```
Input:  ["Brightening", "Fades dark spots"]
Output: ["Reveals a radiant, even-toned complexion...", ...]
```

##### Usage Tool
**File**: `src/services/tools/usage_tool.py`

**LLM**:  Yes (Claude Sonnet 4.5)

**Prompt**:
```
System: Skincare expert
Task: Create detailed usage instructions
Output: JSON array of steps
```

**API Call**: 1 call, ~600 tokens

**Transform**:
```
Input:  "Apply 2-3 drops in the morning"
Output: [
  "Cleanse your face thoroughly...",
  "Apply 2-3 drops to fingertips...",
  "Gently massage into face...",
  ...
]
```

#### Sub-component: Comparison Page Generator

##### Comparison Tool
**File**: `src/services/tools/comparision_tool.py`

**LLM**:  Yes (Claude Sonnet 4.5)

**Prompt**:
```
System: Product comparison expert
Task: Compare two products with analysis
Output: JSON with comparison and verdict
```

**API Call**: 1 call, ~1,200 tokens

**Output**:
```json
{
  "products": {
    "Product A": {...},
    "Product B": {...}
  },
  "key_differences": ["...", "...", "..."],
  "verdict": "..."
}
```

---

### 4. Synthesizer Agent
**File**: `src/services/agents/synthesizer.py`

**Purpose**: Combine all worker outputs into final state

**LLM**:  No (simple data aggregation)

**Output**: Complete state with all generated pages

---

## LLM Service Layer

**File**: `src/services/llm_service.py`

**Purpose**: Centralized Claude API wrapper

**Features**:
-  Singleton pattern (one instance)
-  Environment variable management
-  Error handling
-  Consistent API interface

**Usage**:
```python
from src.services.llm_service import get_llm_service

llm = get_llm_service()
response = llm.generate(system_prompt, user_prompt, max_tokens)
```

---

## State Management

**File**: `src/utils/state.py`

**Type**: LangGraph TypedDict

**Keys**:
```python
{
  "raw_product_data": Dict,  # Input
  "product": Dict,            # Parsed product
  "questions": Dict,          # Generated questions
  "faq_page": Dict,          # FAQ page
  "product_page": Dict,      # Product page
  "comparison_page": Dict,   # Comparison page
  "plan": List,              # Orchestrator plan
}
```

---


---

## Data Flow

```
Raw Product Data
    ↓
[Parse] → Structured Product
    ↓
[Orchestrator] → Task Plan
    ↓
    ├─→ [Question Gen + LLM] → Questions
    │
    └─→ [Page Gen]
        ├─→ [FAQ Gen + LLM] → FAQ Page
        ├─→ [Benefits Tool + LLM] → Enhanced Benefits
        ├─→ [Usage Tool + LLM] → Detailed Steps
        └─→ [Comparison Tool + LLM] → Comparison Analysis
    ↓
[Synthesizer] → Final State
    ↓
JSON Output Files
```


## Extensibility

### Adding New Agents

1. Create agent class in `src/services/agents/`
2. Inherit from `BaseAgent`
3. Implement `run(state)` method
4. Add to workflow in `src/services/graph/workflow.py`

### Adding New Tools

1. Create tool class in `src/services/tools/`
2. Inherit from `BaseTool`
3. Implement `execute()` method
4. Integrate LLM if needed
5. Use in Page Generation Agent

### Adding New Templates

1. Add generation method in `PageGenerationAgent`
2. Create LLM prompt
3. Add to return dictionary
4. Update state schema if needed

---







