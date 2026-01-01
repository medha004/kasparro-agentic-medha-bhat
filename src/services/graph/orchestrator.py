# src/services/graph/orchestrator.py
"""
Dynamic LLM-based orchestrator that reasons about tasks and coordinates agents.
This is a true orchestrator that analyzes state and makes intelligent decisions.
"""
from src.utils.state import AgentState
from src.services.llm_service import get_llm_service
from langgraph.types import Send
import json


class DynamicOrchestrator:
    """
    Intelligent orchestrator that uses LLM reasoning to create dynamic plans.
    """
    
    def __init__(self):
        self.llm = get_llm_service()
        self.available_agents = {
            "parse_product_worker": {
                "capabilities": ["parse_product", "data_transformation"],
                "description": "Transforms raw product JSON into structured data model"
            },
            "question_gen_worker": {
                "capabilities": ["generate_questions", "content_strategy"],
                "description": "Generates categorized user questions using LLM reasoning"
            },
            "page_gen_worker": {
                "capabilities": ["generate_pages", "content_creation", "faq", "product_page", "comparison"],
                "description": "Creates FAQ, product, and comparison pages using content tools"
            },
            "quality_checker": {
                "capabilities": ["quality_check", "validation"],
                "description": "Validates generated content quality and completeness"
            }
        }
    
    def analyze_state_and_plan(self, state: AgentState) -> dict:
        """
        Use LLM to analyze current state and create a dynamic plan.
        This is the core of dynamic orchestration.
        """
        # Build context about current state
        state_summary = self._summarize_state(state)
        
        system_prompt = """You are an intelligent orchestrator for a multi-agent content generation system.

Your job is to analyze the current state and decide which agents need to run and in what order.

Available Agents:
1. parse_product_worker - Transforms raw product data into structured format
2. question_gen_worker - Generates categorized questions about the product  
3. page_gen_worker - Creates FAQ, product description, and comparison pages
4. quality_checker - Validates content quality and completeness

Rules for Planning:
- Only include agents whose work is not yet complete
- Consider dependencies (e.g., questions must exist before FAQ can be generated)
- If content quality is poor (iteration_count exists), consider re-running specific agents
- Be efficient - don't re-run agents unless needed
- Prioritize based on what's missing

Return your analysis as JSON with this structure:
{
  "reasoning": "Your analysis of what needs to be done and why",
  "tasks": [
    {
      "agent": "agent_name",
      "priority": 1,
      "reason": "Why this agent is needed",
      "depends_on": ["agent_name"] or null
    }
  ],
  "estimated_completion": "description of expected final state"
}

CRITICAL: Return ONLY raw JSON, no markdown, no code fences."""

        user_prompt = f"""Analyze this state and create an execution plan:

Current State Summary:
{state_summary}

Available Agents and Capabilities:
{json.dumps(self.available_agents, indent=2)}

What agents should run and in what order? Consider:
1. What data is missing?
2. What dependencies exist between agents?
3. Is this a new run or refinement iteration?
4. What's the most efficient execution plan?

Return your plan as JSON."""

        try:
            response = self.llm.generate(system_prompt, user_prompt, max_tokens=1000)
            plan_data = json.loads(response)
            
            print(f"\n{'='*60}")
            print("ORCHESTRATOR REASONING:")
            print(f"{'='*60}")
            print(plan_data.get("reasoning", "No reasoning provided"))
            print(f"\nPlanned Tasks: {len(plan_data.get('tasks', []))}")
            for task in plan_data.get("tasks", []):
                print(f"  - {task['agent']}: {task['reason']}")
            print(f"{'='*60}\n")
            
            return plan_data
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Orchestrator LLM reasoning failed: {e}")
            # Fallback to basic plan
            return self._create_fallback_plan(state)
    
    def _summarize_state(self, state: AgentState) -> str:
        """Create a concise summary of current state for LLM analysis."""
        summary = []
        
       
        iteration = state.get("iteration_count", 0)
        summary.append(f"\nIteration: {iteration}")
        
        if state.get("needs_refinement"):
            summary.append("Status: Content needs refinement")
        
        completed_tasks = state.get("completed_tasks", [])
        if completed_tasks:
            summary.append(f"\nCompleted tasks: {', '.join(completed_tasks)}")
        
        # Check for recent messages
        messages = state.get("messages", [])
        if messages:
            recent = messages[-3:] if len(messages) > 3 else messages
            summary.append(f"\nRecent messages: {len(recent)}")
            for msg in recent:
                summary.append(f"  - {msg['from_agent']} → {msg['to_agent']}: {msg['message_type']}")
        
        return "\n".join(summary)
    
    def _create_fallback_plan(self, state: AgentState) -> dict:
        """Create a basic plan when LLM reasoning fails."""
        tasks = []
        
        if not state.get("product"):
            tasks.append({
                "agent": "parse_product_worker",
                "priority": 1,
                "reason": "Product data needs to be parsed",
                "depends_on": None
            })
        
        if not state.get("questions"):
            tasks.append({
                "agent": "question_gen_worker", 
                "priority": 2,
                "reason": "Questions need to be generated",
                "depends_on": ["parse_product_worker"] if not state.get("product") else None
            })
        
        if not state.get("faq_page") or not state.get("product_page") or not state.get("comparison_page"):
            tasks.append({
                "agent": "page_gen_worker",
                "priority": 3,
                "reason": "Pages need to be generated",
                "depends_on": ["question_gen_worker"] if not state.get("questions") else None
            })
        
        return {
            "reasoning": "Fallback plan: executing standard content generation pipeline",
            "tasks": tasks,
            "estimated_completion": "All pages generated"
        }


def orchestrator_node(state: AgentState):
    """
    Orchestrator node that analyzes state and creates dynamic plan.
    This replaces the hard-coded static plan with LLM-powered reasoning.
    """
    orchestrator = DynamicOrchestrator()
    
    # Use LLM to analyze state and create plan
    plan_data = orchestrator.analyze_state_and_plan(state)
    
    # Extract tasks from plan
    tasks = plan_data.get("tasks", [])
    
    # Convert to simple task list for state
    plan = [{"type": task["agent"], "reason": task["reason"]} for task in tasks]
    
    return {
        "plan": plan,
        "orchestrator_reasoning": plan_data.get("reasoning", ""),
        "messages": [{
            "from_agent": "orchestrator",
            "to_agent": "broadcast",
            "message_type": "notify",
            "content": {
                "status": "plan_created",
                "task_count": len(tasks),
                "reasoning": plan_data.get("reasoning", "")
            },
            "timestamp": "",
            "reply_to": None
        }]
    }


def assign_workers(state: AgentState):
    """
    Dynamically assign workers based on the orchestrator's plan.
    Workers are dispatched with appropriate context and can coordinate.
    """
    worker_map = {
        "parse_product_worker": "parse_product_worker",
        "question_gen_worker": "question_gen_worker",
        "page_gen_worker": "page_gen_worker",
        "quality_checker": "quality_checker"
    }
    
    sends = []
    plan = state.get("plan", [])
    
    if not plan:
        # No plan means orchestrator decided no work needed
        return []
    
    for task in plan:
        task_type = task["type"]
        node_name = worker_map.get(task_type)
        
        if node_name:
            # Create rich context for each worker
            sends.append(
                Send(
                    node_name,
                    {
                        "task": task,
                        "raw_product_data": state.get("raw_product_data"),
                        "product": state.get("product"),
                        "questions": state.get("questions"),
                        "faq_page": state.get("faq_page"),
                        "product_page": state.get("product_page"),
                        "comparison_page": state.get("comparison_page"),
                        "messages": state.get("messages", []),
                        "iteration_count": state.get("iteration_count", 0)
                    }
                )
            )
    
    return sends
