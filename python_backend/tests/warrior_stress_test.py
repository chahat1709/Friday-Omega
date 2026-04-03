import sys
import os
import json
import unittest
from unittest.mock import MagicMock

# Standard path resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.multi_agent_system import MultiAgentSystem

class MockLLM:
    def generate(self, system_prompt, prompt, temperature=0.1):
        # CEO Logic: Route to NetOps
        if "SUPERVISOR" in system_prompt or "TARGET_AGENT" in prompt:
            return json.dumps({
                "target_agent": "NET_OPS",
                "instruction": "Audit 192.168.1.1 with scanning and stress testing."
            })
        
        # NetOps logic: Delegate to Nmap and StressTester
        if "NETOPS" in system_prompt:
            return json.dumps({
                "mission_status": "in_progress",
                "delegations": [
                    {"expert": "nmap", "task": "Scan ports 1-1000 on 192.168.1.1"},
                    {"expert": "stresstester", "task": "Warrior-grade stress test on 192.168.1.1 port 80"}
                ]
            })
        
        # Risk Officer: Approve everything
        if "RISK OFFICER" in system_prompt or "PlanValidator" in str(type(self)):
            return json.dumps({
                "approved": True,
                "risk_score": 2,
                "concerns": "Minimal risk locally.",
                "recommendations": "Proceed with caution."
            })
            
        return "{}"

    def generate_with_image(self, *args):
        return "Screen shows a terminal and a browser window."

def run_warrior_test():
    print("--- FRIDAY OMEGA: WARRIOR STRESS TEST ---")
    
    # 1. Setup
    mock_llm = MockLLM()
    # Mock HumanoidAgent to avoid browser initialization errors
    mock_worker = MagicMock()
    
    mas = MultiAgentSystem(mock_llm, mock_worker)
    
    # Override validator to use mock logic
    mas.validator.validate_plan = MagicMock(return_value=(True, {"concerns": "NONE"}))
    
    # 2. Execute Mission
    mission = "Strategic command: Perform a network discovery and stress test on target 192.168.1.1. I need a warrior-grade report."
    print(f"\n[CEO] Incoming Mission: {mission}")
    
    result = mas.process_request(mission)
    
    print("\n--- MISSION FINAL REPORT ---")
    print(result)
    print("\n-----------------------------")

if __name__ == "__main__":
    run_warrior_test()
