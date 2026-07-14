"""Deterministic policy engine for Frondly support agent.

This module enforces the Customer Care Guide through deterministic rules.
The LLM is NEVER allowed to decide policy - policy is enforced through code.
"""

import re
from typing import Optional, Tuple


# Policy keywords and patterns - deterministic matching only

LEGAL_KEYWORDS = [
    "lawyer",
    "lawsuit",
    "legal",
    "attorney",
    "chargeback",
    "payment dispute",
    "bbb",
    "ftc",
    "regulator",
    "subpoena",
    "data deletion",
    "privacy request",
    "injury",
    "property damage",
    "demand letter",
    "liability",
    "sue",
    "suing",
    "litigation"
]

SAFETY_KEYWORDS = [
    "ate",
    "chewed",
    "swallowed",
    "ingested",
    "licked",
    "drooling",
    "drool",
    "sick",
    "toxic",
    "toxicity",
    "poison",
    "poisonous",
    "vet",
    "veterinary",
    "emergency",
    "er",
    "aspca",
    "poison control"
]

SAFETY_SUBJECTS = [
    "dog",
    "cat",
    "pet",
    "child",
    "kid",
    "baby",
    "toddler",
    "human",
    "puppy",
    "kitten"
]

PRESS_KEYWORDS = [
    "influencer",
    "followers",
    "press",
    "journalist",
    "media",
    "partnership",
    "interview",
    "article",
    "story",
    "coverage",
    "social media",
    "youtube",
    "tiktok",
    "instagram"
]

PROMPT_INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"system:",
    r"developer:",
    r"issue full refund",
    r"as an ai",
    r"as an assistant",
    r"override",
    r"admin",
    r"debug",
    r"system prompt",
    r"instruction",
    r"comply with reasonable",
    r"formally instructing",
    r"required to comply"
]


class PolicyEngine:
    """Deterministic policy enforcement engine."""
    
    def __init__(self):
        """Initialize the policy engine."""
        self.legal_pattern = self._compile_pattern(LEGAL_KEYWORDS)
        self.safety_pattern = self._compile_pattern(SAFETY_KEYWORDS)
        self.press_pattern = self._compile_pattern(PRESS_KEYWORDS)
        self.injection_patterns = [re.compile(pattern, re.IGNORECASE) 
                                   for pattern in PROMPT_INJECTION_PATTERNS]
    
    def _compile_pattern(self, keywords: list) -> re.Pattern:
        """Compile a regex pattern from keywords."""
        pattern = r"\b(" + "|".join(re.escape(kw) for kw in keywords) + r")\b"
        return re.compile(pattern, re.IGNORECASE)
    
    def check_red_lines(self, message: str) -> Tuple[bool, Optional[str]]:
        """Check if message triggers any red line escalation.
        
        Returns:
            Tuple of (is_red_line, escalation_category)
        """
        # Check for legal keywords
        if self.legal_pattern.search(message):
            return True, "legal"
        
        # Check for safety/ingestion issues
        if self._check_safety(message):
            return True, "safety"
        
        # Check for press/influencer
        if self.press_pattern.search(message):
            return True, "press"
        
        # Check for prompt injection
        if self._check_prompt_injection(message):
            # This is still a red line, but treated as other/policy
            return True, "other"
        
        return False, None
    
    def _check_safety(self, message: str) -> bool:
        """Check for safety/ingestion concerns."""
        message_lower = message.lower()
        
        # Check if safety keywords are present
        has_safety_keyword = self.safety_pattern.search(message)
        
        # Check if subject (pet/child) is mentioned
        has_subject = any(subject in message_lower for subject in SAFETY_SUBJECTS)
        
        # Safety concern only if both are present
        return bool(has_safety_keyword and has_subject)
    
    def _check_prompt_injection(self, message: str) -> bool:
        """Check for prompt injection patterns."""
        for pattern in self.injection_patterns:
            if pattern.search(message):
                return True
        return False
    
    def check_refund_ceiling(self, current_total: float, new_amount: float) -> bool:
        """Check if refund would exceed $50 conversation ceiling.
        
        Args:
            current_total: Current refund total in conversation
            new_amount: New refund amount being requested
            
        Returns:
            True if refund would exceed ceiling, False otherwise
        """
        return (current_total + new_amount) > 50.0
    
    def check_verification_required(self, action: str) -> bool:
        """Check if action requires verification.
        
        Args:
            action: The action being attempted (refund, account_change, etc.)
            
        Returns:
            True if verification is required
        """
        verification_required_actions = [
            "refund",
            "account_change",
            "subscription",
            "cancel",
            "pause",
            "address_change",
            "email_change",
            "tier_change"
        ]
        return action in verification_required_actions
    
    def is_policy_compliant_refund(self, reason: str, has_photo: bool, 
                                   days_since_delivery: int) -> Tuple[bool, str]:
        """Check if refund request complies with policy.
        
        Args:
            reason: The reason for refund
            has_photo: Whether customer has provided photo
            days_since_delivery: Days since delivery
            
        Returns:
            Tuple of (is_compliant, explanation)
        """
        # COA (Crispy-on-Arrival) policy
        if "crispy" in reason.lower() or "dead" in reason.lower() or \
           "damaged" in reason.lower() or "shattered" in reason.lower() or \
           "broken" in reason.lower() or "cracked" in reason.lower():
            
            # Must be within 14 days
            if days_since_delivery > 14:
                return False, "Outside 14-day window for COA claims"
            
            # Photo required for refund, otherwise needs human
            if not has_photo:
                return False, "Photo required for COA refund (replacement path available)"
            
            return True, "COA claim within policy"
        
        # Other reasons need human review
        return False, "Reason requires human review"
    
    def check_privacy_violation(self, message: str, verified: bool, 
                                asking_about_another: bool) -> Tuple[bool, Optional[str]]:
        """Check for privacy violations.
        
        Args:
            message: Customer message
            verified: Whether customer is verified
            asking_about_another: Whether asking about another customer's data
            
        Returns:
            Tuple of (is_violation, escalation_category)
        """
        if asking_about_another:
            if not verified:
                return True, "privacy"
            # Even if verified, cannot reveal another customer's data
            return True, "privacy"
        
        return False, None