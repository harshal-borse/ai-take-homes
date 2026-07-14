"""Agent state for the Frondly support agent."""

from typing import TypedDict, Optional, List


class AgentState(TypedDict):
    """State for the Frondly support agent conversation."""
    
    # Conversation identification
    conversation_id: str
    
    # Verification status
    verified: bool
    customer_id: Optional[str]
    email: Optional[str]
    
    # Escalation status
    escalation_required: bool
    escalation_category: Optional[str]
    escalation_latch: bool  # Once escalated, never resume normal service
    
    # Refund tracking
    refund_total: float
    
    # Intent classification
    intent: str
    
    # Tool actions taken
    tool_actions: List[dict]
    
    # Agent response to customer
    response: str
    
    # Customer message
    customer_message: str
    
    # Conversation turn counter
    turn_count: int