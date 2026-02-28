"""HydraExpert — Real brute-force auditing via ToolExecutor."""
import logging
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.experts.base_expert import BaseExpert
from core.llm import LLMEngine

class HydraExpert(BaseExpert):
    """Tier 4 Specialist: Runs REAL hydra brute-force via ToolExecutor."""
    
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Hydra Specialist", llm_engine)
        self.system_prompt = "YOU ARE THE HYDRA SPECIALIST. Crack authentication on target services."

    def execute_task(self, task_instruction: str) -> str:
        logging.info(f"[HydraExpert] Real brute-force: {task_instruction}")
        
        # Parse target and service
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', task_instruction)
        target = ips[0] if ips else "127.0.0.1"
        
        service = "ssh"  # default
        for svc in ["ssh", "ftp", "telnet", "mysql", "rdp", "http", "smb"]:
            if svc in task_instruction.lower():
                service = svc
                break
        
        try:
            result = self.tools.run_hydra(target, service=service)
            
            if not result.success:
                return self.log_result(f"HYDRA FAILED: {result.error}")
            
            if result.data.get("cracked"):
                creds = result.data.get("credentials_found", [])
                output = f"HYDRA SUCCESS on {target} ({service}):\n"
                for c in creds:
                    output += f"  Login: {c['login']} / Password: {c['password']}\n"
                return self.log_result(output)
            else:
                return self.log_result(f"HYDRA COMPLETE on {target} ({service}): No weak credentials found.")
                
        except Exception as e:
            return self.log_result(f"HYDRA EXECUTION ERROR: {e}")
