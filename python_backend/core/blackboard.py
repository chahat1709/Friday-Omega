import json
import logging
import threading
from typing import Dict, List, Any, Optional, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Blackboard:
    """
    Tier 1 Central Ledger.
    All agents in the 1000+ hierarchy post intelligence here.
    No agent communicates directly with another; they read/write to the Blackboard.
    """
    
    def __init__(self):
        # A thread-safe lock since multiple agents (threads) might write simultaneously
        self._lock = threading.Lock()
        
        # The main intelligence ledger
        self.ledger: List[Dict[str, Any]] = []
        
        # Attack Graph / State Tracker (Target -> Ports/Vulns/Creds)
        self.state_tracker: Dict[str, Dict[str, Any]] = {}
        
        # Pub/Sub callbacks (e.g., C-Suite Directors waiting for specific intel)
        self.subscribers: Dict[str, set] = {}

    def post_intel(self, agent_id: str, intel_type: str, data: Any, confidence: int = 100, target: Optional[str] = None):
        """
        An agent posts findings to the board.
        Args:
            agent_id (str): e.g., 'Agent_405_SQLi'
            intel_type (str): e.g., 'port_scan', 'vulnerability', 'credential'
            data (Any): The actual data found.
            confidence (int): 0-100 indicating mathematical certainty.
            target (str): The IP/Domain this intel relates to.
        """
        # Enforce confidence bounds
        confidence = max(0, min(100, confidence))
        
        entry = {
            "agent_id": agent_id,
            "intel_type": intel_type,
            "data": data,
            "confidence": confidence,
            "target": target
        }
        
        with self._lock:
            self.ledger.append(entry)
            
            # Update the Attack Graph (State Tracker) if applicable
            if target:
                if target not in self.state_tracker:
                    self.state_tracker[target] = {"ports": [], "vulns": [], "creds": []}
                
                if intel_type == "port_scan":
                    self.state_tracker[target]["ports"].append({"data": data, "confidence": confidence})
                elif intel_type == "vulnerability":
                    self.state_tracker[target]["vulns"].append({"data": data, "confidence": confidence})
                elif intel_type == "credential":
                    self.state_tracker[target]["creds"].append({"data": data, "confidence": confidence})
        
        logging.info(f"[BLACKBOARD] Intel Posted ({confidence}% Conf) | From: {agent_id} | Type: {intel_type}")
        
        # Trigger any subscribers waiting for this specific type of intel
        self._notify_subscribers(intel_type, entry)

    def get_intel(self, intel_type: Optional[str] = None, min_confidence: int = 0) -> List[Dict[str, Any]]:
        """
        Agents or the Commander can read intel from the board.
        """
        with self._lock:
            if not intel_type:
                return [entry for entry in self.ledger if entry["confidence"] >= min_confidence]
            
            return [
                entry for entry in self.ledger 
                if entry["intel_type"] == intel_type and entry["confidence"] >= min_confidence
            ]

    def subscribe(self, intel_type: str, callback_function: Callable):
        """
        Allow Captains/Directors to subscribe to specific intel (e.g., wake up if a password is found).
        """
        with self._lock:
            if intel_type not in self.subscribers:
                self.subscribers[intel_type] = set()
            self.subscribers[intel_type].add(callback_function)

    def _notify_subscribers(self, intel_type: str, entry: Dict[str, Any]):
        """Internal method to trigger callbacks."""
        # Need to copy to release lock before executing callbacks
        with self._lock:
            callbacks = self.subscribers.get(intel_type, set()).copy()
            
        for callback in callbacks:
            try:
                callback(entry)
            except Exception as e:
                logging.error(f"[BLACKBOARD] Error in subscriber callback: {e}")

    def export_state(self) -> str:
        """Returns the current attack graph as a JSON string for the CEO/Commander to read."""
        with self._lock:
            return json.dumps(self.state_tracker, indent=4)

# Global singleton so all agents access the same board
blackboard = Blackboard()
