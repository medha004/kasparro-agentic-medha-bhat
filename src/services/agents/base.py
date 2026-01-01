# src/services/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.utils.messages import Message, MessageType, MessageBus


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system.
    
    Each agent is autonomous and can:
    - Decide if it should activate based on current state
    - Communicate with other agents via messages
    - Request help or information from other agents
    - Execute its core competency
    """

    name: str = "base-agent"
    capabilities: List[str] = []  # What this agent can do
    
    def __init__(self):
        """Initialize agent with message bus reference."""
        self.message_bus = MessageBus()

    @abstractmethod
    def should_activate(self, state: Dict[str, Any]) -> bool:
        """
        Determine if this agent should activate based on current state.
        This enables agent autonomy - agents decide when they're needed.
        
        Args:
            state: Current workflow state
            
        Returns:
            True if agent should run, False otherwise
        """
        pass

    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent's core logic.
        
        Args:
            state: Current LangGraph state
            
        Returns:
            Partial state update
        """
        pass
    
    def read_messages(self, state: Dict[str, Any]) -> List[Message]:
        """
        Read messages addressed to this agent from state.
        
        Args:
            state: Current state containing messages
            
        Returns:
            List of Message objects for this agent
        """
        messages_data = state.get("messages", [])
        messages = []
        for msg_data in messages_data:
            if msg_data["to_agent"] == self.name or msg_data["to_agent"] == "broadcast":
                msg = Message(
                    from_agent=msg_data["from_agent"],
                    to_agent=msg_data["to_agent"],
                    message_type=MessageType(msg_data["message_type"]),
                    content=msg_data["content"],
                    timestamp=msg_data["timestamp"],
                    reply_to=msg_data.get("reply_to")
                )
                messages.append(msg)
        return messages
    
    def send_message(self, to_agent: str, message_type: MessageType, 
                    content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a message to another agent.
        
        Args:
            to_agent: Name of target agent or "broadcast"
            message_type: Type of message
            content: Message content
            
        Returns:
            State update with new message
        """
        message = Message(
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )
        return {"messages": [message.to_dict()]}
    
    def can_handle(self, task_type: str) -> bool:
        """
        Check if this agent can handle a specific task type.
        
        Args:
            task_type: Type of task
            
        Returns:
            True if agent has this capability
        """
        return task_type in self.capabilities

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Makes agent compatible with LangGraph nodes.
        First checks if agent should activate, then runs if needed.
        """
        # Check messages first - agent might be specifically requested
        messages = self.read_messages(state)
        has_request = any(msg.message_type == MessageType.REQUEST for msg in messages)
        
        # Activate if requested OR if agent determines it should
        if has_request or self.should_activate(state):
            result = self.run(state)
            
            # Add notification that this agent completed its work
            notification = self.send_message(
                to_agent="broadcast",
                message_type=MessageType.NOTIFY,
                content={"status": "completed", "agent": self.name}
            )
            
            # Merge notification into result
            if "messages" in result:
                result["messages"].extend(notification["messages"])
            else:
                result["messages"] = notification["messages"]
            
            return result
        else:
            # Agent decided not to activate - return minimal state update
            return {
                "messages": [self.send_message(
                    to_agent="orchestrator",
                    message_type=MessageType.NOTIFY,
                    content={"status": "skipped", "agent": self.name, "reason": "not_needed"}
                )["messages"][0]]
            }
