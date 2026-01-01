# src/utils/messages.py
"""
Message passing system for agent-to-agent communication.
Enables agents to communicate, request help, and coordinate dynamically.
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class MessageType(Enum):
    """Types of messages agents can send."""
    REQUEST = "request"  # Request another agent to perform work
    RESPONSE = "response"  # Response to a request
    NOTIFY = "notify"  # Notify other agents of completion
    QUERY = "query"  # Query for information
    PROPOSAL = "proposal"  # Propose a plan or action


@dataclass
class Message:
    """A message between agents."""
    from_agent: str
    to_agent: str  # Can be "broadcast" for all agents
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reply_to: Optional[str] = None  # ID of message being replied to
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "reply_to": self.reply_to
        }


class MessageBus:
    """
    Central message bus for agent communication.
    Agents post messages here and retrieve messages addressed to them.
    """
    
    def __init__(self):
        self.messages: List[Message] = []
    
    def post(self, message: Message):
        """Post a message to the bus."""
        self.messages.append(message)
    
    def get_messages_for(self, agent_name: str, 
                         message_type: Optional[MessageType] = None) -> List[Message]:
        """
        Get all messages for a specific agent.
        Optionally filter by message type.
        """
        filtered = [
            msg for msg in self.messages
            if (msg.to_agent == agent_name or msg.to_agent == "broadcast")
        ]
        
        if message_type:
            filtered = [msg for msg in filtered if msg.message_type == message_type]
        
        return filtered
    
    def get_latest_from(self, from_agent: str) -> Optional[Message]:
        """Get the latest message from a specific agent."""
        matches = [msg for msg in self.messages if msg.from_agent == from_agent]
        return matches[-1] if matches else None
    
    def clear(self):
        """Clear all messages (for new workflow run)."""
        self.messages.clear()
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert all messages to dictionaries."""
        return [msg.to_dict() for msg in self.messages]
