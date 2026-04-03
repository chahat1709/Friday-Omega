import sys
import os
import json
from unittest.mock import MagicMock

# Standard path resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.multi_agent_system import MultiAgentSystem

class MockLLM:
    def generate(self, system_prompt, prompt, temperature=0.1):
        # FieldOps logic: Delegate to Flipper
        if "FIELDOPS" in system_prompt:
            return json.dumps({
                "mission_status": "in_progress",
                "delegations": [
                    {"expert": "flipper", "task": "Clone the 125kHz RFID badge in proximity."}
                ]
            })
        return "{}"

def run_physical_mission_test():
    print("--- FRIDAY OMEGA: REAL MISSION TEST (PHYSICAL) ---")
    
    # 1. Setup
    mock_llm = MockLLM()
    mock_worker = MagicMock()
    
    mas = MultiAgentSystem(mock_llm, mock_worker)
    
    # Override validator for bypass
    mas.validator.validate_plan = MagicMock(return_value=(True, {}))
    
    # 2. Execute Physical Mission
    mission = "Strategic command: Use the physical Flipper asset to clone the target's RFID badge."
    print(f"\n[CEO] Incoming Physical Mission: {mission}")
    
    result = mas.process_request(mission)
    
    print("\n--- MISSION FINAL REPORT ---")
    print(result)
    print("\n-----------------------------")

if __name__ == "__main__":
    run_physical_mission_test()
