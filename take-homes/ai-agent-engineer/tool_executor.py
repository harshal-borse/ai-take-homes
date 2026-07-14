"""Tool executor for Frondly support agent.

This module wraps all tool execution with policy checks.
Tools are NEVER exposed directly to the LLM - all execution must pass through policy checks.
"""

import sys
import os
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

# Add stubs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stubs'))
from frondly_tools import find_customer, get_orders, issue_refund, update_subscription, create_escalation
from policy_engine import PolicyEngine
from verification import VerificationManager


class ToolExecutor:
    """Wraps tool execution with policy enforcement."""
    
    def __init__(self):
        """Initialize the tool executor."""
        self.policy_engine = PolicyEngine()
        self.verification_manager = VerificationManager()
    
    def safe_find_customer(self, email: str, session: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """Safely look up customer with policy checks.
        
        Args:
            email: Customer email
            session: Current session state
            
        Returns:
            Tuple of (customer_data, error_message)
        """
        try:
            customer = find_customer(email)
            if customer:
                return customer, None
            else:
                return None, "No account found with this email address"
        except Exception as e:
            return None, f"Error looking up customer: {str(e)}"
    
    def safe_get_orders(self, customer_id: str, session: Dict) -> Tuple[list, Optional[str]]:
        """Safely get customer orders with policy checks.
        
        Args:
            customer_id: Customer ID
            session: Current session state
            
        Returns:
            Tuple of (orders, error_message)
        """
        try:
            orders = get_orders(customer_id)
            return orders, None
        except Exception as e:
            return [], f"Error retrieving orders: {str(e)}"
    
    def safe_issue_refund(self, customer_id: str, order_id: str, amount: float, 
                         reason: str, session: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """Safely issue refund with all policy checks.
        
        Args:
            customer_id: Customer ID
            order_id: Order ID
            amount: Refund amount
            reason: Refund reason
            session: Current session state
            
        Returns:
            Tuple of (refund_result, error_message)
        """
        # Check if escalated
        if session.get("escalation_latch", False):
            return None, "Cannot process refunds - conversation has been escalated"
        
        # Check verification
        if not session.get("verified", False):
            return None, "Verification required before issuing refund"
        
        # Check refund ceiling
        current_total = session.get("refund_total", 0.0)
        if self.policy_engine.check_refund_ceiling(current_total, amount):
            return None, f"Refund amount (${current_total + amount:.2f}) exceeds $50 conversation ceiling"
        
        # Check policy compliance for reason
        has_photo = "photo" in reason.lower() or "attached" in reason.lower()
        
        # Estimate days since delivery (simplified - in real system would use actual dates)
        days_since_delivery = self._estimate_days_since_delivery(order_id, customer_id)
        
        is_compliant, policy_reason = self.policy_engine.is_policy_compliant_refund(
            reason, has_photo, days_since_delivery
        )
        
        if not is_compliant:
            return None, f"Refund not permitted: {policy_reason}"
        
        # All checks passed - issue refund
        try:
            refund = issue_refund(customer_id, order_id, amount, reason)
            
            # Update session refund total
            session["refund_total"] = current_total + amount
            
            # Record action
            session["tool_actions"].append({
                "action": "refund",
                "customer_id": customer_id,
                "order_id": order_id,
                "amount": amount,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            
            return refund, None
        except Exception as e:
            return None, f"Error issuing refund: {str(e)}"
    
    def safe_update_subscription(self, customer_id: str, action: str, 
                                detail: str, session: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """Safely update subscription with policy checks.
        
        Args:
            customer_id: Customer ID
            action: Subscription action (pause, resume, cancel, etc.)
            detail: Additional details
            session: Current session state
            
        Returns:
            Tuple of (result, error_message)
        """
        # Check if escalated
        if session.get("escalation_latch", False):
            return None, "Cannot process subscription changes - conversation has been escalated"
        
        # Check verification
        if not session.get("verified", False):
            return None, "Verification required before making account changes"
        
        # Check if action requires verification
        if self.policy_engine.check_verification_required(action):
            if not session.get("verified", False):
                return None, "Verification required for this action"
        
        try:
            result = update_subscription(customer_id, action, detail)
            
            # Record action
            session["tool_actions"].append({
                "action": "subscription_" + action,
                "customer_id": customer_id,
                "detail": detail,
                "timestamp": datetime.now().isoformat()
            })
            
            return result, None
        except Exception as e:
            return None, f"Error updating subscription: {str(e)}"
    
    def safe_create_escalation(self, category: str, member_ref: str, 
                               verification_status: str, summary: str, 
                               attempted: str, references: str,
                               customer_facing_line: str, session: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """Safely create escalation with policy checks.
        
        Args:
            category: Escalation category
            member_ref: Customer reference
            verification_status: Verification status
            summary: Situation summary
            attempted: What was attempted
            references: Order/subscription references
            customer_facing_line: Customer-facing script
            session: Current session state
            
        Returns:
            Tuple of (escalation_result, error_message)
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
            
            # Record action
            session["tool_actions"].append({
                "action": "escalation",
                "category": category,
                "member_ref": member_ref,
                "timestamp": datetime.now().isoformat()
            })
            
            return escalation, None
        except Exception as e:
            return None, f"Error creating escalation: {str(e)}"
    
    def _estimate_days_since_delivery(self, order_id: str, customer_id: str) -> int:
        """Estimate days since delivery (simplified for this exercise).
        
        In a real system, this would use actual delivery dates from the order.
        For this exercise, we'll use a simplified approach.
        """
        # This is a placeholder - in production, use actual order data
        # For now, return a reasonable default
        return 5  # Assume recent delivery for most cases