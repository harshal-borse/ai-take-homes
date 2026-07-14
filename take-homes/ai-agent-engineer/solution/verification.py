"""Verification logic for Frondly support agent.

This module handles customer identity verification according to the Customer Care Guide:
- Email on the account
- PLUS either the most recent order number OR the name of a plant/item in their most recent box
"""

import re
from typing import Optional, Dict, List
import sys
import os

# Add stubs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stubs'))
from frondly_tools import find_customer, get_orders


class VerificationManager:
    """Manages customer verification process."""
    
    def __init__(self):
        """Initialize the verification manager."""
        self.verified_customers = {}  # Session-based verification cache
    
    def extract_email(self, message: str) -> Optional[str]:
        """Extract email address from message.
        
        Args:
            message: Customer message
            
        Returns:
            Email address if found, None otherwise
        """
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, message)
        return match.group(0) if match else None
    
    def extract_order_number(self, message: str) -> Optional[str]:
        """Extract order number from message.
        
        Args:
            message: Customer message
            
        Returns:
            Order number if found, None otherwise
        """
        # Order pattern: ORD-XXXX
        order_pattern = r'\bORD-\d{4,5}\b'
        match = re.search(order_pattern, message, re.IGNORECASE)
        return match.group(0).upper() if match else None
    
    def verify_customer(self, email: str, order_number: Optional[str] = None, 
                       plant_name: Optional[str] = None) -> Dict:
        """Attempt to verify customer.
        
        Args:
            email: Customer email
            order_number: Optional order number for verification
            plant_name: Optional plant name for verification
            
        Returns:
            Dict with verification result and customer data if successful
        """
        # Look up customer by email
        customer = find_customer(email)
        
        if not customer:
            return {
                "verified": False,
                "customer_id": None,
                "reason": "No account found with this email"
            }
        
        # If no verification factors provided, request them
        if not order_number and not plant_name:
            return {
                "verified": False,
                "customer_id": customer["id"],
                "reason": "Verification required - please provide order number or plant name from recent box",
                "customer": customer
            }
        
        # Get customer's orders (most recent first)
        orders = get_orders(customer["id"])
        
        if not orders:
            return {
                "verified": False,
                "customer_id": customer["id"],
                "reason": "No orders found on account",
                "customer": customer
            }
        
        most_recent_order = orders[0]
        
        # Verify by order number
        if order_number:
            if order_number.upper() == most_recent_order["order_id"]:
                return {
                    "verified": True,
                    "customer_id": customer["id"],
                    "customer": customer,
                    "verified_via": "order_number",
                    "verified_value": order_number
                }
            else:
                # Check if order number exists in their order history
                order_ids = [o["order_id"] for o in orders]
                if order_number.upper() in order_ids:
                    return {
                        "verified": True,
                        "customer_id": customer["id"],
                        "customer": customer,
                        "verified_via": "order_number",
                        "verified_value": order_number
                    }
                else:
                    return {
                        "verified": False,
                        "customer_id": customer["id"],
                        "reason": "Order number not found in your order history",
                        "customer": customer
                    }
        
        # Verify by plant name
        if plant_name:
            plant_lower = plant_name.lower()
            for item in most_recent_order["items"]:
                if plant_lower in item["name"].lower():
                    return {
                        "verified": True,
                        "customer_id": customer["id"],
                        "customer": customer,
                        "verified_via": "plant_name",
                        "verified_value": item["name"]
                    }
            
            # Check other orders too
            for order in orders[1:]:
                for item in order["items"]:
                    if plant_lower in item["name"].lower():
                        return {
                            "verified": True,
                            "customer_id": customer["id"],
                            "customer": customer,
                            "verified_via": "plant_name",
                            "verified_value": item["name"]
                        }
            
            return {
                "verified": False,
                "customer_id": customer["id"],
                "reason": "Plant name not found in your recent orders",
                "customer": customer
            }
        
        return {
            "verified": False,
            "customer_id": customer["id"],
            "reason": "Verification failed",
            "customer": customer
        }
    
    def check_verification_persistence(self, session: Dict) -> bool:
        """Check if customer is already verified in this session.
        
        Args:
            session: Current session state
            
        Returns:
            True if verified, False otherwise
        """
        return session.get("verified", False)
    
    def get_verification_status(self, session: Dict) -> Dict:
        """Get current verification status from session.
        
        Args:
            session: Current session state
            
        Returns:
            Dict with verification status details
        """
        return {
            "verified": session.get("verified", False),
            "customer_id": session.get("customer_id"),
            "email": session.get("email"),
            "verified_via": session.get("verified_via"),
            "verified_value": session.get("verified_value")
        }