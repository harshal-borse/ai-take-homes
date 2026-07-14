"""Frondly support agent - main entry point.

This module implements the respond() function expected by the harness.
The agent uses a LangGraph workflow to process customer messages.
"""

import re
import sys
import os
from typing import Dict

# Add local modules to path
sys.path.insert(0, os.path.dirname(__file__))

from state import AgentState
from graph import FrondlyAgentGraph
from verification import VerificationManager
from intent_classifier import IntentClassifier
from care_advice import CareAdvisor
from policy_engine import PolicyEngine
from escalation import EscalationEngine
from tool_executor import ToolExecutor


class FrondlyAgent:
    """Main Frondly support agent."""
    
    def __init__(self):
        """Initialize the agent with all components."""
        self.graph_builder = FrondlyAgentGraph()
        self.verification_manager = VerificationManager()
        self.intent_classifier = IntentClassifier()
        self.care_advisor = CareAdvisor()
        self.policy_engine = PolicyEngine()
        self.escalation_engine = EscalationEngine()
        self.tool_executor = ToolExecutor()
    
    def respond(self, session: Dict, message: str) -> str:
        """Process a customer message and return a response.
        
        This is the main function called by the harness.
        
        Args:
            session: Per-conversation session dict (owned by agent)
            message: Customer message
            
        Returns:
            Agent response to customer
        """
        # Initialize session if needed
        self._initialize_session(session)
        
        # Check if already escalated - if so, return standard escalation response
        if self.escalation_engine.is_escalated(session):
            return self.escalation_engine.get_escalation_response(session)
        
        # Process message through the agent workflow
        response = self._process_message(session, message)
        
        # Update turn counter
        session["turn_count"] = session.get("turn_count", 0) + 1
        
        return response
    
    def _initialize_session(self, session: Dict) -> None:
        """Initialize session state if not already set.
        
        Args:
            session: Session dict to initialize
        """
        # Set defaults if not present
        session.setdefault("verified", False)
        session.setdefault("customer_id", None)
        session.setdefault("email", None)
        session.setdefault("escalation_required", False)
        session.setdefault("escalation_category", None)
        session.setdefault("escalation_latch", False)
        session.setdefault("refund_total", 0.0)
        session.setdefault("intent", "general")
        session.setdefault("tool_actions", [])
        session.setdefault("turn_count", 0)
    
    def _process_message(self, session: Dict, message: str) -> str:
        """Process message through the agent decision workflow.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Agent response
        """
        # Check for red lines first (immediate escalation)
        is_red_line, category = self.policy_engine.check_red_lines(message)
        if is_red_line:
            return self._handle_immediate_escalation(session, category, message)
        
        # Extract verification information
        email = self.verification_manager.extract_email(message)
        order_number = self.verification_manager.extract_order_number(message)
        
        # Handle verification if email provided
        if email and not session.get("verified"):
            verification_result = self._handle_verification(
                session, email, order_number, message
            )
            if not verification_result["verified"]:
                return self._request_verification()
            else:
                # Successfully verified, provide acknowledgment
                return f"Perfect! I've verified your account. How can I help you today?"
        
        # Classify intent
        intent = self.intent_classifier.classify(message)
        session["intent"] = intent
        
        # Route to appropriate handler
        if intent == "care_advice":
            return self._handle_care_advice(message)
        elif intent == "refund":
            return self._handle_refund_request(session, message)
        elif intent == "subscription":
            return self._handle_subscription_request(session, message)
        elif intent == "account_change":
            return self._handle_account_change(session, message)
        elif intent == "shipping":
            return self._handle_shipping_inquiry(session, message)
        elif intent == "legal":
            return self._handle_legal_escalation(session, message)
        elif intent == "safety":
            return self._handle_safety_escalation(session, message)
        elif intent == "press":
            return self._handle_press_escalation(session, message)
        elif intent == "privacy":
            return self._handle_privacy_escalation(session, message)
        else:
            # For general messages, check if they're continuations
            return self._handle_contextual_response(session, message)
    
    def _handle_immediate_escalation(self, session: Dict, category: str, 
                                     message: str) -> str:
        """Handle immediate red line escalation.
        
        Args:
            session: Current session state
            category: Escalation category
            message: Customer message
            
        Returns:
            Escalation response
        """
        session["escalation_required"] = True
        session["escalation_category"] = category
        
        # Create escalation
        member_ref = session.get("customer_id", "unverified caller")
        verification_status = "verified" if session.get("verified") else "unverified"
        
        summary = f"Red line escalation: {category}. Customer message: {message[:200]}"
        attempted = "Agent identified red line policy violation"
        references = session.get("conversation_id", "")
        customer_facing_line = self.escalation_engine.get_customer_facing_line(category)
        
        self.tool_executor.safe_create_escalation(
            category, member_ref, verification_status, summary,
            attempted, references, customer_facing_line, session
        )
        
        # Set escalation latch
        self.escalation_engine.set_escalation_latch(session)
        
        return customer_facing_line
    
    def _handle_verification(self, session: Dict, email: str, 
                            order_number: str, message: str) -> Dict:
        """Handle customer verification.
        
        Args:
            session: Current session state
            email: Customer email
            order_number: Order number if provided
            message: Customer message
            
        Returns:
            Verification result dict
        """
        # Extract plant name if no order number
        plant_name = None
        if not order_number:
            # Simple extraction - would be more sophisticated in production
            plant_keywords = ["monstera", "calathea", "pothos", "fern", "fiddle", "palm", "plant"]
            for keyword in plant_keywords:
                if keyword in message.lower():
                    plant_name = keyword
                    break
        
        result = self.verification_manager.verify_customer(
            email, order_number, plant_name
        )
        
        if result["verified"]:
            session["verified"] = True
            session["customer_id"] = result["customer_id"]
            session["email"] = email
            session["verified_via"] = result.get("verified_via")
            session["verified_value"] = result.get("verified_value")
        
        return result
    
    def _request_verification(self) -> str:
        """Request verification from customer.
        
        Returns:
            Verification request message
        """
        return "I'd be happy to help! To verify your account, could you please provide your email address along with either your most recent order number or the name of a plant from your latest box?"
    
    def _handle_care_advice(self, message: str) -> str:
        """Handle care advice requests.
        
        Args:
            message: Customer message
            
        Returns:
            Care advice response
        """
        advice = self.care_advisor.get_advice(message)
        if advice:
            return advice
        
        return "I'd be happy to help with plant care! Could you tell me more about what's going on with your plant? For example, are you seeing yellow leaves, brown tips, or any specific issues?"
    
    def _handle_refund_request(self, session: Dict, message: str) -> str:
        """Handle refund requests.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Refund response
        """
        # Check verification
        if not session.get("verified"):
            return self._request_verification()
        
        # Extract refund details (simplified)
        # In production, would use NLP to extract specific amounts and order IDs
        amount = self._extract_amount(message)
        order_id = self.verification_manager.extract_order_number(message)
        
        if not order_id:
            order_id = session.get("most_recent_order", "ORD-XXXX")
        
        # Check refund ceiling
        current_total = session.get("refund_total", 0.0)
        if self.policy_engine.check_refund_ceiling(current_total, amount or 0):
            # Escalate due to ceiling
            return self._handle_escalation_for_ceiling(session, amount, current_total)
        
        # Process refund
        customer_id = session.get("customer_id")
        reason = message
        
        result, error = self.tool_executor.safe_issue_refund(
            customer_id, order_id, amount or 0, reason, session
        )
        
        if error:
            if "ceiling" in error.lower():
                return self._handle_escalation_for_ceiling(session, amount, current_total)
            elif "photo" in error.lower():
                return "I can help with that! For crispy or damaged plants, I'll need a photo to process the refund. Could you attach a photo of the plant? Alternatively, I can arrange a replacement if you prefer."
            else:
                return f"I apologize, but I'm unable to process this refund: {error}"
        
        return f"I've processed your refund of ${amount or 0:.2f}. You should see it reflected on your original payment method within 3-5 business days. Is there anything else I can help with?"
    
    def _extract_amount(self, message: str) -> float:
        """Extract monetary amount from message.
        
        Args:
            message: Customer message
            
        Returns:
            Extracted amount or 0 if not found
        """
        # Look for dollar amounts
        amount_pattern = r'\$(\d+\.?\d*)'
        match = re.search(amount_pattern, message)
        if match:
            return float(match.group(1))
        return 0.0
    
    def _handle_escalation_for_ceiling(self, session: Dict, amount: float, 
                                       current_total: float) -> str:
        """Handle escalation due to refund ceiling.
        
        Args:
            session: Current session state
            amount: Requested refund amount
            current_total: Current refund total
            
        Returns:
            Escalation response
        """
        session["escalation_required"] = True
        session["escalation_category"] = "refund_ceiling"
        
        # Create escalation
        member_ref = session.get("customer_id", "unverified caller")
        verification_status = "verified" if session.get("verified") else "unverified"
        
        summary = f"Refund request exceeding $50 ceiling. Requested: ${amount:.2f}, Current total: ${current_total:.2f}"
        attempted = f"Agent processed ${current_total:.2f} in refunds, remaining ${amount:.2f} exceeds ceiling"
        references = session.get("conversation_id", "")
        customer_facing_line = self.escalation_engine.get_customer_facing_line("refund_ceiling")
        
        self.tool_executor.safe_create_escalation(
            "refund_ceiling", member_ref, verification_status, summary,
            attempted, references, customer_facing_line, session
        )
        
        self.escalation_engine.set_escalation_latch(session)
        
        return customer_facing_line
    
    def _handle_subscription_request(self, session: Dict, message: str) -> str:
        """Handle subscription change requests.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Subscription response
        """
        # Check verification
        if not session.get("verified"):
            return self._request_verification()
        
        # Determine action
        action = self._determine_subscription_action(message)
        customer_id = session.get("customer_id")
        
        result, error = self.tool_executor.safe_update_subscription(
            customer_id, action, message, session
        )
        
        if error:
            return f"I apologize, but I'm unable to process this change: {error}"
        
        action_responses = {
            "pause": "I've paused your subscription. You won't be charged while paused, and you can resume whenever you're ready.",
            "resume": "I've resumed your subscription. Your next box will ship according to the normal schedule.",
            "cancel": "I've cancelled your subscription. You'll receive a confirmation email shortly."
        }
        
        return action_responses.get(action, "I've processed your subscription change. Is there anything else I can help with?")
    
    def _determine_subscription_action(self, message: str) -> str:
        """Determine subscription action from message.
        
        Args:
            message: Customer message
            
        Returns:
            Action string
        """
        message_lower = message.lower()
        if "pause" in message_lower:
            return "pause"
        elif "resume" in message_lower:
            return "resume"
        elif "cancel" in message_lower:
            return "cancel"
        return "pause"
    
    def _handle_account_change(self, session: Dict, message: str) -> str:
        """Handle account change requests.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Account change response
        """
        # Check verification
        if not session.get("verified"):
            return self._request_verification()
        
        customer_id = session.get("customer_id")
        
        # Determine change type
        if "address" in message.lower():
            action = "change_address"
        elif "email" in message.lower():
            action = "change_email"
        else:
            action = "change_address"
        
        result, error = self.tool_executor.safe_update_subscription(
            customer_id, action, message, session
        )
        
        if error:
            return f"I apologize, but I'm unable to process this change: {error}"
        
        return f"I've updated your account. The change will take effect for your next box. Is there anything else I can help with?"
    
    def _handle_shipping_inquiry(self, session: Dict, message: str) -> str:
        """Handle shipping inquiries.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Shipping inquiry response
        """
        if not session.get("verified"):
            return self._request_verification()
        
        # Check for specific shipping concerns
        message_lower = message.lower()
        if "lost" in message_lower or "where" in message_lower:
            return "I'd be happy to check on your shipment. Based on the tracking, your order is still in transit but hasn't moved as expected. Let me flag this for investigation. You should receive an update within 24-48 hours."
        elif "slow" in message_lower or "delayed" in message_lower:
            return "I see the tracking hasn't updated recently. This can happen sometimes during shipping. Your order is still in the shipping window and should arrive soon. If you don't receive it by the expected delivery date, please reach out and we'll investigate further."
        else:
            return "I'd be happy to help with your shipping question. Your order is currently in transit and should arrive according to the normal delivery schedule. Is there a specific concern about the shipment?"
    
    def _handle_legal_escalation(self, session: Dict, message: str) -> str:
        """Handle legal escalation.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Legal escalation response
        """
        return self._handle_immediate_escalation(session, "legal", message)
    
    def _handle_safety_escalation(self, session: Dict, message: str) -> str:
        """Handle safety/ingestion escalation.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Safety escalation response
        """
        return self._handle_immediate_escalation(session, "safety", message)
    
    def _handle_press_escalation(self, session: Dict, message: str) -> str:
        """Handle press escalation.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Press escalation response
        """
        return self._handle_immediate_escalation(session, "press", message)
    
    def _handle_privacy_escalation(self, session: Dict, message: str) -> str:
        """Handle privacy escalation.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Privacy escalation response
        """
        return self._handle_immediate_escalation(session, "privacy", message)
    
    def _handle_general_inquiry(self, session: Dict, message: str) -> str:
        """Handle general inquiries.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            General response
        """
        return "Thank you for reaching out! I'm here to help with your Frondly account, orders, plant care questions, or any other concerns. What can I assist you with today?"
    
    def _handle_contextual_response(self, session: Dict, message: str) -> str:
        """Handle contextual responses for general messages.
        
        Args:
            session: Current session state
            message: Customer message
            
        Returns:
            Contextually appropriate response
        """
        # Check if this is a thank you or closing
        message_lower = message.lower()
        if any(word in message_lower for word in ["thank", "thanks", "appreciate", "great"]):
            return "You're very welcome! I'm glad I could help. Is there anything else I can assist you with today?"
        
        # Check if this is an acknowledgment
        if any(word in message_lower for word in ["ok", "got it", "noted", "cool", "alright"]):
            return "Great! Is there anything else I can help you with?"
        
        # Default to general inquiry
        return self._handle_general_inquiry(session, message)


# Create agent instance for harness
_agent = FrondlyAgent()

def respond(session: dict, message: str) -> str:
    """Process a customer message and return a response.
    
    This is the main function called by the harness.
    
    Args:
        session: Per-conversation session dict (owned by agent)
        message: Customer message
        
    Returns:
        Agent response to customer
    """
    return _agent.respond(session, message)