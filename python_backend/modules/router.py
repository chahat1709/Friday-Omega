"""Simple Router to classify text intents into CHAT or ACT.
This is a lightweight classifier—replace with an LLM-based router later.
"""
from typing import Literal

KEYWORDS_ACT = ["open", "play", "click", "type", "search", "send", "spotify", "youtube", "whatsapp"]

class Router:
    @staticmethod
    def classify(text: str) -> Literal["CHAT", "ACT"]:
        if not text:
            return "CHAT"
        lower = text.lower()
        # simple heuristic: if any action keyword present -> ACT
        for kw in KEYWORDS_ACT:
            if kw in lower:
                return "ACT"
        return "CHAT"
