"""Intent classifier for Frondly support agent.

This module classifies customer intents using deterministic keyword matching.
Recommended approach: simple keyword rules for stability over LLM classification.
"""

import re
from typing import Optional


class IntentClassifier:
    """Classifies customer intents using keyword matching."""
    
    def __init__(self):
        """Initialize the intent classifier with keyword patterns."""
        
        # Define intent keywords
        self.intent_patterns = {
            "refund": [
                r"\brefund\b",
                r"\bmoney back\b",
                r"\bcredit\b",
                r"\breimburse\b",
                r"\breturn\b",
                r"\bchargeback\b"
            ],
            "subscription": [
                r"\bpause\b",
                r"\bresume\b",
                r"\bcancel\b",
                r"\bsubscription\b",
                r"\bunsubscribe\b",
                r"\bskip\b",
                r"\bchange tier\b",
                r"\bupgrade\b",
                r"\bdowngrade\b"
            ],
            "account_change": [
                r"\baddress\b",
                r"\bemail\b",
                r"\bphone\b",
                r"\bchange\b",
                r"\bupdate\b",
                r"\bshipping\b"
            ],
            "care_advice": [
                r"\bcare\b",
                r"\bwater\b",
                r"\blight\b",
                r"\byellow\b",
                r"\bbrown\b",
                r"\bcrispy\b",
                r"\bleaves\b",
                r"\bgnats\b",
                r"\bmites\b",
                r"\brepot\b",
                r"\bhow to\b",
                r"\bhow do i\b",
                r"\badvice\b",
                r"\bhelp\b",
                r"\bnormal\b"
            ],
            "verification": [
                r"\bverify\b",
                r"\bconfirm\b",
                r"\baccount\b",
                r"\border number\b",
                r"\bORD-\b"
            ],
            "shipping": [
                r"\bwhere\b",
                r"\btracking\b",
                r"\bshipped\b",
                r"\bdelivery\b",
                r"\bbox\b",
                r"\bpackage\b",
                r"\blate\b",
                r"\blost\b"
            ],
            "legal": [
                r"\blawyer\b",
                r"\blawsuit\b",
                r"\blegal\b",
                r"\battorney\b",
                r"\bchargeback\b",
                r"\bftc\b",
                r"\bbb\b",
                r"\bregulator\b",
                r"\bliability\b",
                r"\bsue\b"
            ],
            "safety": [
                r"\bate\b",
                r"\bchewed\b",
                r"\bswallowed\b",
                r"\bingested\b",
                r"\btoxic\b",
                r"\bpoison\b",
                r"\bvet\b",
                r"\bpoison control\b"
            ],
            "press": [
                r"\binfluencer\b",
                r"\bfollowers\b",
                r"\bpress\b",
                r"\bjournalist\b",
                r"\bmedia\b",
                r"\bpartnership\b"
            ],
            "privacy": [
                r"\bdata deletion\b",
                r"\bdelete\b",
                r"\bprivacy\b",
                r"\bgdpr\b",
                r"\bccpa\b",
                r"\berasure\b"
            ]
        }
        
        # Compile patterns
        self.compiled_patterns = {}
        for intent, patterns in self.intent_patterns.items():
            self.compiled_patterns[intent] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def classify(self, message: str) -> str:
        """Classify the intent of a customer message.
        
        Args:
            message: Customer message
            
        Returns:
            Intent classification string
        """
        message_lower = message.lower()
        
        # Check each intent category
        intent_scores = {}
        for intent, patterns in self.compiled_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(message):
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        
        # Return highest scoring intent, or "general" if none
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return "general"
    
    def get_intent_confidence(self, message: str, intent: str) -> float:
        """Get confidence score for a specific intent.
        
        Args:
            message: Customer message
            intent: Intent to check
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if intent not in self.compiled_patterns:
            return 0.0
        
        patterns = self.compiled_patterns[intent]
        matches = sum(1 for pattern in patterns if pattern.search(message))
        return min(matches / len(patterns), 1.0) if patterns else 0.0