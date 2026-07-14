"""Escalation engine for Frondly support agent.

This module handles escalation creation and management according to the Customer Care Guide.
Once escalated, the agent never resumes normal service in that conversation.
"""

import sys
import os
from typing import Dict, Optional

# Add stubs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stubs'))
from frondly_tools import create_escalation


class EscalationEngine:
    """Manages escalation creation and the escalation latch."""
    
    def __init__(self):
        """Initialize the escalation engine."""
        self.escalation_scripts = {
            "legal": "I hear you, and I'm sorry this happened. This is something a human teammate needs to handle personally. I'm escalating it right now with everything you've told me, and someone will contact you at the email on file. I'm not able to discuss it further here, but you're in good hands.",
            "safety": "I'm not able to give medical or veterinary advice, and I don't want to guess about safety. Please contact your vet or the ASPCA Animal Poison Control Center at (888) 426-4435 (for pets) or Poison Control at 1-800-222-1222 (for people) right away. I'm connecting you with a human teammate now, and I've flagged this as urgent.",
            "refund_ceiling": "I understand this is frustrating, but refunds over $50 require review from a human teammate. I'm escalating this with all the details, and someone will be in touch soon.",
            "verification": "For account security, I need to verify your identity before making changes. Since we haven't completed verification, I'll need to connect you with a human teammate who can help with account recovery.",
            "privacy": "For privacy and security reasons, I can't reveal information about other accounts. A human teammate will need to review this request.",
            "press": "Thanks for your interest! For press, influencer, and partnership inquiries, please reach out to press@frondly.example. I'm connecting you with our team for follow-up.",
            "other": "I understand, and I want to make sure this gets the right attention. I'm escalating this to a human teammate who can help you further."
        }
    
    def build_escalation(self, category: str, member_ref: str, 
                        verification_status: str, summary: str, 
                        attempted: str, references: str,
                        customer_facing_line: str) -> Dict:
        """Build and record an escalation.
        
        Args:
            category: Escalation category (legal, safety, refund_ceiling, etc.)
            member_ref: Customer reference (customer_id or "unverified caller")
            verification_status: Verification status at time of escalation
            summary: One-paragraph summary of the situation
            attempted: What was already said/attempted
            references: Relevant order/subscription references
            customer_facing_line: The customer-facing line used
            
        Returns:
            Dict containing the escalation record
        """
        try:
            escalation = create_escalation(
                category=category,
                member_ref=member_ref,
                verification_status=verification_status,
                summary=summary,
                attempted=attempted,
                references=references,
                customer_facing_line=customer_facing_line
            )
            return escalation
        except ValueError as e:
            # Log the error and return a failure indicator
            return {
                "error": str(e),
                "failed": True
            }
    
    def get_customer_facing_line(self, category: str) -> str:
        """Get the appropriate customer-facing script for an escalation.
        
        Args:
            category: Escalation category
            
        Returns:
            Customer-facing script
        """
        return self.escalation_scripts.get(category, self.escalation_scripts["other"])
    
    def should_escalate(self, session: Dict, category: str) -> bool:
        """Determine if escalation should occur based on session state.
        
        Args:
            session: Current session state
            category: Proposed escalation category
            
        Returns:
            True if should escalate, False if already escalated
        """
        # Once escalated, never escalate again
        if session.get("escalation_latch", False):
            return False
        
        return True
    
    def set_escalation_latch(self, session: Dict) -> Dict:
        """Set the escalation latch to prevent future actions.
        
        Args:
            session: Current session state
            
        Returns:
            Updated session state
        """
        session["escalation_latch"] = True
        session["escalation_required"] = True
        return session
    
    def is_escalated(self, session: Dict) -> bool:
        """Check if conversation has been escalated.
        
        Args:
            session: Current session state
            
        Returns:
            True if escalated, False otherwise
        """
        return session.get("escalation_latch", False)
    
    def get_escalation_response(self, session: Dict) -> str:
        """Get the standard response for an escalated conversation.
        
        Args:
            session: Current session state
            
        Returns:
            Standard escalation response
        """
        if session.get("escalation_category"):
            script = self.get_customer_facing_line(session["escalation_category"])
            return script
        return self.escalation_scripts["other"]