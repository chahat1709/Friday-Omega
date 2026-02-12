import logging
from typing import Any, Dict

class FailsafeEngine:
    """
    Tier 1 Strategic Command: The Dead Man's Switch.
    Provides deterministic (non-AI) fallbacks for when the primary brains are offline.
    """
    
    def __init__(self):
        # Basic patterns for hardcoded intent detection
        self.fallback_intents = {
            "scan": "NETWORK_SCAN",
            "nmap": "NETWORK_SCAN",
            "whois": "RECON",
            "sqlmap": "WEB_VULN",
            "hack": "NETWORK_SCAN", # Safe fallback: just scan first
            "help": "SYSTEM_INFO"
        }

    def get_fallback_action(self, user_input: str) -> Dict[str, Any]:
        """
        Attempts to find a safe, non-AI interpretation of the user's input.
        """
        logging.warning(f"[FAILSAFE] Brains offline. Attempting deterministic fallback for: '{user_input}'")
        
        user_input_lower = user_input.lower()
        
        for keyword, intent in self.fallback_intents.items():
            if keyword in user_input_lower:
                return {
                    "intent": intent,
                    "confidence": 0.5, # Low confidence because it's a fallback
                    "source": "failsafe_engine",
                    "instruction": f"Deterministic execution of {intent} based on keyword '{keyword}'"
                }
        
        return {
            "intent": "CHAT",
            "confidence": 0.1,
            "source": "failsafe_engine",
            "instruction": "I am operating in DEGRADED MODE. AI brains are currently offline. I can only handle basic scan/recon commands."
        }

failsafe = FailsafeEngine()
