"""Action Engine: executes parsed actions using existing Tools and actuator.
This is a minimal implementation that maps common actions to Tools methods.
"""
from core.tools import Tools
from typing import Dict, Any
from .vision_agent import VisionAgent

class ActionEngine:
    def __init__(self):
        self.tools = Tools
        self.vision_agent = VisionAgent()

    def handle(self, text: str, simulate: bool = False) -> Dict[str, Any]:
        """Handle an action-oriented text command.
        Prefer the VisionAgent loop for ACT intents. In simulate mode no GUI is triggered.
        """
        lower = text.lower()

        # If it's a music play request, prefer the existing Tools with simulate=False only if allowed
        if "liked songs" in lower or ("play" in lower and "liked" in lower):
            # Use VisionAgent to locate UI elements in simulated mode by default
            result = self.vision_agent.run_task("Open Spotify and play liked songs", simulate=simulate)
            return {"status": "ok", "result": result}

        if lower.startswith("play "):
            song = text[5:].strip()
            # If simulate, run VisionAgent; otherwise call Tools directly
            if simulate:
                result = self.vision_agent.run_task(f"Play {song} on Spotify or YouTube", simulate=True)
                return {"status": "ok", "result": result}
            else:
                res = self.tools.play_music(song)
                return {"status": "ok", "result": res}

        if lower.startswith("open "):
            app = text[5:].strip()
            if simulate:
                result = self.vision_agent.run_task(f"Open {app} from start menu", simulate=True)
                return {"status": "ok", "result": result}
            else:
                res = self.tools.open_app(app)
                return {"status": "ok", "result": res}

        return {"status": "error", "result": "Unknown action."}
