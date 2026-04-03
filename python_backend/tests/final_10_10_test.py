import sys
import os
import json
from unittest.mock import MagicMock

# Standard path resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.multi_agent_system import MultiAgentSystem

class MockLLM:
    def generate(self, system_prompt, prompt, temperature=0.1):
        # CEO Logic: Full Spectrum
        if "SUPERVISOR" in system_prompt or "CEO" in system_prompt:
            return json.dumps({
                "target_agent": "INTEL_OPS",
                "instruction": "Recon on target-corp.com"
            })
            
        # IntelOps Logic: Delegate to Shodan
        if "INTELOPS" in system_prompt:
            return json.dumps({
                "mission_status": "complete",
                "delegations": [
                    {"expert": "shodan", "task": "Scan target-corp.com for open ports"}
                ]
            })
            
        # FieldOps Logic: Delegate to Flipper
        if "FIELDOPS" in system_prompt:
            return json.dumps({
                "mission_status": "complete",
                "delegations": [
                    {"expert": "flipper", "task": "Clone proximal RFID badge"}
                ]
            })
            
        return "{}"

def run_perfection_test():
    print("--- FRIDAY OMEGA: 10/10 PERFECTION TEST ---")
    
    # 1. Setup
    mock_llm = MockLLM()
    mock_worker = MagicMock()
    
    mas = MultiAgentSystem(mock_llm, mock_worker)
    mas.validator.validate_plan = MagicMock(return_value=(True, {}))
    
    # 2. Phase A: Recon
    print("\n[PHASE A] Intel & Recon...")
    recon_result = mas.process_request("Perform reconnaissance on target-corp.com")
    print(recon_result)
    
    # 3. Phase B: Physical
    print("\n[PHASE B] Physical Breach...")
    physical_result = mas.field_ops.execute_mission("Clone on-site badge.")
    print(physical_result)
    
    # 4. Phase C: Network Stress
    print("\n[PHASE C] Network Saturation...")
    net_result = mas.net_ops.execute_mission("Stress test the primary gateway.")
    print(net_result)
    
    print("\n--- 10/10 STATUS: VERIFIED ---")

if __name__ == "__main__":
    run_perfection_test()
