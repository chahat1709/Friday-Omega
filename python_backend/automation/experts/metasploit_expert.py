"""MetasploitExpert — Real exploitation via ToolExecutor."""
import logging
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.experts.base_expert import BaseExpert
from core.llm import LLMEngine

class MetasploitExpert(BaseExpert):
    """Tier 4 Specialist: Runs REAL metasploit modules via ToolExecutor."""
    
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Metasploit Specialist", llm_engine)
        self.system_prompt = """YOU ARE THE METASPLOIT SPECIALIST.
        Given a task, output the exact MSF module path and RHOSTS option.
        Format: MODULE=exploit/... RHOSTS=x.x.x.x"""

    def execute_task(self, task_instruction: str) -> str:
        logging.info(f"[MetasploitExpert] Real exploit: {task_instruction}")
        
        # Ask LLM for the right module
        llm_response = self.llm.generate(
            system_prompt=self.system_prompt,
            prompt=f"Target task: {task_instruction}. Provide the MSF module and options."
        )
        
        # Parse module from LLM response
        module_match = re.search(r'(exploit/\S+|auxiliary/\S+|post/\S+)', llm_response)
        module = module_match.group(1) if module_match else "auxiliary/scanner/portscan/tcp"
        
        # Parse options
        options = {}
        opt_matches = re.findall(r'(\w+)=([\d\.\w/]+)', llm_response)
        for key, value in opt_matches:
            options[key.upper()] = value
        
        # Extract target IP from instruction as fallback
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', task_instruction)
        if ips and "RHOSTS" not in options:
            options["RHOSTS"] = ips[0]
        
        try:
            result = self.tools.run_metasploit(module, options)
            
            if not result.success:
                return self.log_result(f"MSF FAILED: {result.error}")
            
            return self.log_result(f"MSF MODULE: {module}\n{result.raw_output[:2000]}")
            
        except Exception as e:
            return self.log_result(f"MSF EXECUTION ERROR: {e}")
