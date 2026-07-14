"""Care advice module for Frondly support agent.

This module provides hardcoded care advice from the Customer Care Guide appendix.
No vector database or RAG required - simple keyword matching.
"""

import re
from typing import Optional, List


# Care guide from Customer Care Guide §9
CARE_GUIDE = {
    "yellow leaves": {
        "keywords": ["yellow", "yellowing", "yellow leaves", "yellowing leaves"],
        "advice": "Yellow leaves on monstera, pothos, and most tropicals are usually from overwatering. Check that soil dries about 2 inches down between waterings, ensure the pot has drainage, and remove fully yellow leaves."
    },
    "brown tips": {
        "keywords": ["brown", "crispy", "crispy tips", "brown tips", "browning", "dried out"],
        "advice": "Brown crispy tips on calathea and ferns are usually from low humidity or tap-water minerals. Try misting the plant or using a pebble tray, and use filtered water if possible."
    },
    "leggy": {
        "keywords": ["leggy", "leaning", "reaching", "leaning toward", "growing tall"],
        "advice": "Leggy growth means insufficient light. Move the plant to a brighter spot, but avoid direct scorching sun for calatheas and ferns. Rotate the plant periodically for even growth."
    },
    "fungus gnats": {
        "keywords": ["gnats", "flies", "flying", "tiny flies", "fruit flies", "soil flies"],
        "advice": "For fungus gnats: let the topsoil dry out between waterings, use sticky traps, and water from the bottom (place pot in a saucer of water)."
    },
    "spider mites": {
        "keywords": ["spider mites", "mites", "webbing", "tiny webs"],
        "advice": "For spider mites: shower the plant to wash them off, wipe the leaves with a damp cloth, and apply neem oil according to the label instructions."
    },
    "repotting": {
        "keywords": ["repot", "repotting", "pot size", "bigger pot", "potting"],
        "advice": "Repot in spring, use a pot 1-2 inches larger than the current one, use fresh potting mix, and water lightly after repotting."
    },
    "watering": {
        "keywords": ["water", "watering", "how often", "when to water", "overwatering", "underwatering"],
        "advice": "Most houseplants prefer to dry out slightly between waterings. Check soil moisture by sticking your finger about 2 inches into the soil - if it's dry, it's time to water. Ensure pots have drainage holes."
    },
    "light": {
        "keywords": ["light", "sunlight", "bright", "direct sun", "indirect light"],
        "advice": "Most tropical plants prefer bright, indirect light. Avoid direct scorching sun, especially for calatheas and ferns. If growth is leggy, the plant likely needs more light."
    }
}


class CareAdvisor:
    """Provides care advice based on keyword matching."""
    
    def __init__(self):
        """Initialize the care advisor."""
        self.care_guide = CARE_GUIDE
        # Compile patterns for matching
        self.patterns = {}
        for topic, data in self.care_guide.items():
            pattern = r"\b(" + "|".join(re.escape(kw) for kw in data["keywords"]) + r")\b"
            self.patterns[topic] = re.compile(pattern, re.IGNORECASE)
    
    def get_advice(self, message: str) -> Optional[str]:
        """Get care advice based on message content.
        
        Args:
            message: Customer message
            
        Returns:
            Care advice if relevant topic found, None otherwise
        """
        message_lower = message.lower()
        
        # Check each topic for keyword matches
        for topic, pattern in self.patterns.items():
            if pattern.search(message):
                return self.care_guide[topic]["advice"]
        
        return None
    
    def get_relevant_topics(self, message: str) -> List[str]:
        """Get list of care topics mentioned in message.
        
        Args:
            message: Customer message
            
        Returns:
            List of relevant topic names
        """
        relevant = []
        for topic, pattern in self.patterns.items():
            if pattern.search(message):
                relevant.append(topic)
        return relevant
    
    def is_care_question(self, message: str) -> bool:
        """Check if message is asking for care advice.
        
        Args:
            message: Customer message
            
        Returns:
            True if message appears to be a care question
        """
        care_indicators = [
            "how do i", "how to", "care", "help", "advice", 
            "normal", "worried", "wrong", "problem", "issue"
        ]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in care_indicators)