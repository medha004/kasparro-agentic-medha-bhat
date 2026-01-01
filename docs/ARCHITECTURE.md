# Multi-Agent System Architecture

## Executive Summary

This document describes a **multi-agent system** that demonstrates enterprise-grade agentic architecture.


## System Components

### 1. Dynamic Orchestrator (`orchestrator.py`)

**Purpose**: Analyze state and create intelligent execution plans

**Key Innovation**: Uses LLM to reason about what needs to be done

```python
class DynamicOrchestrator:
    def analyze_state_and_plan(self, state):
        # LLM analyzes current state
        state_summary = self._summarize_state(state)
        
        # LLM creates plan based on reasoning
        system_prompt = """
        You are an intelligent orchestrator.
        Analyze the state and decide which agents need to run.
        """
        
        plan_data = self.llm.generate(system_prompt, state_summary)
        # Returns: reasoning, tasks, priorities, dependencies
```

**Output**:
```json
{
  "reasoning": "Product is parsed but questions are missing. Need to generate questions before pages.",
  "tasks": [
    {
      "agent": "question_gen_worker",
      "priority": 1,
      "reason": "Questions needed for FAQ generation",
      "depends_on": null
    },
    {
      "agent": "page_gen_worker",
      "priority": 2,
      "reason": "All pages need to be generated",
      "depends_on": ["question_gen_worker"]
    }
  ]
}
```

### 2. Autonomous Agents (`base.py` + agent implementations)

**Base Agent Class**:
```python
class BaseAgent(ABC):
    capabilities: List[str] = []
    
    @abstractmethod
    def should_activate(self, state) -> bool:
        """Agent decides if it should run"""
        pass
    
    def can_handle(self, task_type: str) -> bool:
        """Check if agent has capability"""
        return task_type in self.capabilities
    
    def send_message(self, to_agent, message_type, content):
        """Send message to another agent"""
        pass
    
    def read_messages(self, state) -> List[Message]:
        """Read messages addressed to this agent"""
        pass
```

**Agent Autonomy Features**:

#### Parse Product Agent
```python
def should_activate(self, state) -> bool:
    # Skip if already parsed
    if state.get("product"):
        return False
    
    # Activate if requested
    messages = self.read_messages(state)
    if any(msg.content.get("action") == "reparse" for msg in messages):
        return True
    
    return True  # Activate if not parsed
```

#### Question Generation Agent  
```python
def should_activate(self, state) -> bool:
    # Skip if questions exist
    if state.get("questions"):
        return False
    
    # Activate if regeneration requested
    if self._check_for_regeneration_request(state):
        return True
    
    return True
```

#### Page Generation Agent
```python
def should_activate(self, state) -> bool:
    # Check which pages are missing
    has_faq = state.get("faq_page") is not None
    has_product = state.get("product_page") is not None
    has_comparison = state.get("comparison_page") is not None
    
    # Activate only if something is missing
    if not (has_faq and has_product and has_comparison):
        return True
    
    # Or if refinement requested
    return self._check_for_refinement_request(state)
```


### 3. Message Passing System (`messages.py`)

**Message Types**:
```python
class MessageType(Enum):
    REQUEST = "request"    # Request work from another agent
    RESPONSE = "response"  # Respond to a request
    NOTIFY = "notify"      # Announce completion
    QUERY = "query"        # Ask for information
    PROPOSAL = "proposal"  # Propose a plan or action
```

**Message Structure**:
```python
@dataclass
class Message:
    from_agent: str
    to_agent: str          # Can be "broadcast" for all
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: str
    reply_to: Optional[str]
```

**Usage Examples**:

**Agent requesting help**:
```python
# Page agent needs questions
return self.send_message(
    to_agent="question_gen_worker",
    message_type=MessageType.REQUEST,
    content={"action": "generate", "reason": "Need questions for FAQ"}
)
```

**Agent announcing completion**:
```python
# Parse agent notifies product is ready
notification = self.send_message(
    to_agent="broadcast",
    message_type=MessageType.NOTIFY,
    content={
        "status": "product_parsed",
        "product_name": product["name"]
    }
)
```

**Quality checker requesting refinement**:
```python
# Quality issues found
messages_to_send.append({
    "from_agent": self.name,
    "to_agent": "page_gen_worker",
    "message_type": "request",
    "content": {
        "action": "refine",
        "target": "faq_page",
        "reason": "Need at least 4 Q&As"
    }
})
```



### 4. Adaptive Routing (`workflow.py`)

**Dynamic Route Functions**:

```python
def route_after_orchestrator(state):
    """Route based on orchestrator's plan"""
    plan = state.get("plan", [])
    
    if not plan:
        return "synthesizer"  # Nothing to do
    
    # Check first task in plan
    first_task = plan[0]["type"]
    
    if first_task == "parse_product_worker":
        return "parse_product"
    elif first_task == "question_gen_worker":
        return "questions"
    elif first_task == "page_gen_worker":
        return "pages"
```

```python
def route_after_quality(state):
    """Route after quality check - may loop back"""
    if state.get("needs_refinement"):
        iteration = state.get("iteration_count", 0)
        if iteration < 2:
            return "orchestrator"  # CYCLICAL - go back
    
    return "synthesizer"  # Continue forward
```

```python
def route_after_synthesis(state):
    """Final decision - end or refine"""
    needs_refinement = state.get("needs_refinement")
    
    if needs_refinement is False:
        return "END"
    elif needs_refinement and iteration < 2:
        return "orchestrator"  # CYCLICAL - more work needed
    
    return "END"  # Max iterations reached
```

**Workflow Graph**:
```python
# Conditional edges enable adaptive routing
builder.add_conditional_edges(
    "orchestrator",
    route_after_orchestrator,
    {
        "parse_product": "parse_product_worker",
        "questions": "question_gen_worker",
        "pages": "page_gen_worker",
        "synthesizer": "synthesizer"
    }
)

# Cyclical flow for refinement
builder.add_conditional_edges(
    "quality_checker",
    route_after_quality,
    {
        "orchestrator": "orchestrator",  # LOOP BACK
        "synthesizer": "synthesizer"
    }
)

### 5. Quality Checker Agent (`quality_checker.py`)

**Purpose**: Validate content and trigger iterative refinement

**Autonomy**:
```python
def should_activate(self, state) -> bool:
    iteration = state.get("iteration_count", 0)
    
    # Don't exceed max iterations
    if iteration >= self.max_iterations:
        return False
    
    # Activate if pages exist but not checked yet
    has_pages = (state.get("faq_page") and 
                 state.get("product_page") and 
                 state.get("comparison_page"))
    
    already_checked = "quality_check" in state.get("completed_tasks", [])
    
    return has_pages and not already_checked
```

**Validation Logic**:
```python
def run(self, state):
    issues = []
    
    # Check FAQ quality
    faq_items = state.get("faq_page", {}).get("items", [])
    if len(faq_items) < 4:
        issues.append("FAQ too short")
    
    # Check product page
    benefits = state.get("product_page", {}).get("benefits", [])
    if len(benefits) < 2:
        issues.append("Insufficient benefits")
    
    # If issues and under max iterations, request refinement
    if issues and iteration < self.max_iterations - 1:
        return {
            "needs_refinement": True,
            "iteration_count": iteration + 1,
            "messages": [refinement_requests]
        }
    else:
        return {
            "needs_refinement": False,
            "completed_tasks": ["quality_check"]
        }
```



### 6. State Management (`state.py`)

**Multi-Agent State**:
```python
class AgentState(TypedDict, total=False):
    # Data
    raw_product_data: Dict[str, Any]
    product: Dict[str, Any]
    questions: Dict[str, Any]
    faq_page: Dict[str, Any]
    product_page: Dict[str, Any]
    comparison_page: Dict[str, Any]
    
    # Coordination
    plan: List[Dict[str, Any]]           # Dynamic plan
    messages: List[Dict[str, Any]]        # Agent messages
    completed_tasks: List[str]            # Task tracking
    
    # Workflow control
    iteration_count: int                  # Refinement iterations
    needs_refinement: bool                # Quality flag
    orchestrator_reasoning: str           # Plan reasoning
```


## Execution Flows

### Scenario 1: First Run (All Content New)

```
START
  ↓
[Orchestrator]
  • Analyzes: No product, no questions, no pages
  • Plans: [parse_product, generate_questions, generate_pages]
  ↓
[Router] → routes to parse_product_worker
  ↓
[Parse Product Agent]
  • should_activate() → TRUE (product missing)
  • Parses product data
  • Sends NOTIFY message: "product_parsed"
  ↓
[Router] → routes to question_gen_worker
  ↓
[Question Gen Agent]
  • should_activate() → TRUE (questions missing)
  • Generates 15+ questions
  • Sends NOTIFY message: "questions_ready"
  ↓
[Router] → routes to page_gen_worker
  ↓
[Page Gen Agent]
  • should_activate() → TRUE (pages missing)
  • Generates FAQ, Product, Comparison pages
  • Sends NOTIFY message: "pages_generated"
  ↓
[Router] → routes to quality_checker
  ↓
[Quality Checker]
  • should_activate() → TRUE (content ready, not checked)
  • Validates content
  • No issues found
  • Sets needs_refinement = FALSE
  ↓
[Router] → routes to synthesizer
  ↓
[Synthesizer]
  • should_activate() → TRUE (all content ready)
  • Combines all outputs
  • Validates completeness
  ↓
[Router] → routes to END
  ↓
END (Success)
```

### Scenario 2: Refinement Run (Quality Issues)

```
START
  ↓
[Orchestrator]
  • Analyzes: Product ✓, Questions ✓, Pages ✓
  • Previous iteration: 0
  • Plans: [quality_check]
  ↓
... (same as Scenario 1 until Quality Checker)
  ↓
[Quality Checker]
  • should_activate() → TRUE
  • Validates content
  • Issues found: FAQ has only 3 Q&As (needs 4+)
  • Sends REQUEST to page_gen_worker: "refine faq_page"
  • Sets needs_refinement = TRUE
  • iteration_count = 1
  ↓
[Router] → routes BACK to orchestrator (CYCLICAL)
  ↓
[Orchestrator]
  • Analyzes: iteration_count = 1, needs_refinement = TRUE
  • Plans: [page_gen_worker] (only pages need work)
  ↓
[Router] → routes to page_gen_worker
  ↓
[Page Gen Agent]
  • Reads messages: REQUEST from quality_checker
  • should_activate() → TRUE (refinement requested)
  • Regenerates FAQ page
  • Sends NOTIFY: "refinement_complete"
  ↓
[Router] → routes to quality_checker
  ↓
[Quality Checker]
  • should_activate() → TRUE (iteration < max)
  • Validates again
  • Issues resolved
  • Sets needs_refinement = FALSE
  ↓
[Router] → routes to synthesizer
  ↓
[Synthesizer] → END
```

### Scenario 3: Partial Run (Only FAQ Missing)

```
START
  ↓
[Orchestrator]
  • Analyzes: Product ✓, Questions ✓, Product Page ✓, Comparison ✓
  •           FAQ Page ✗
  • Plans: [page_gen_worker] (only FAQ needed)
  ↓
[Router] → routes to page_gen_worker (skips parse & questions)
  ↓
[Page Gen Agent]
  • should_activate() → TRUE (FAQ missing)
  • Generates ONLY FAQ page (skips others)
  • Sends NOTIFY: "faq_generated"
  ↓
[Router] → routes to quality_checker
  ↓
[Quality Checker] → Synthesizer → END
```

---




## Performance Characteristics

### First Run (All New Content)
- **Agents Activated**: 5 (Parse, Question, Page, Quality, Synthesizer)
- **LLM Calls**: 6-7 (Orchestrator, Questions, FAQ, Benefits, Usage, Comparison)
- **Messages Sent**: ~10 notifications
- **Iterations**: 1

### Refinement Run (Quality Issues)
- **Agents Activated**: 3-4 (Orchestrator, affected agent, Quality, Synthesizer)
- **LLM Calls**: 2-4 (Orchestrator, specific content regeneration)
- **Messages Sent**: ~5 (requests + notifications)
- **Iterations**: 2-3 (original + refinements)

### Partial Run (One Component Missing)
- **Agents Activated**: 2-3 (only needed agents + Quality + Synthesizer)
- **LLM Calls**: 2-3 (Orchestrator + specific generation)
- **Messages Sent**: ~5
- **Iterations**: 1

---

## Extensibility

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement `should_activate()` for autonomy
3. Implement `run()` for core logic
4. Declare `capabilities`
5. Add to orchestrator's `available_agents`
6. Add routing logic in workflow

Example:
```python
class SummaryAgent(BaseAgent):
    name = "summary_agent"
    capabilities = ["summarize", "condense"]
    
    def should_activate(self, state):
        # Activate if summary missing
        return not state.get("summary")
    
    def run(self, state):
        # Generate summary
        summary = self.llm.generate(...)
        return {"summary": summary}
```

### Adding New Message Types

1. Add to `MessageType` enum
2. Implement handling in agents
3. Update router if needed

### Adding New Tools

1. Create tool class inheriting from `BaseTool`
2. Implement `execute()` method
3. Integrate into relevant agent

---



