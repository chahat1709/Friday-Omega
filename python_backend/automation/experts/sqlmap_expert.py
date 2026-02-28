"""SqlmapExpert — Real SQL injection testing via ToolExecutor."""
import logging
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.experts.base_expert import BaseExpert
from core.llm import LLMEngine

class SqlmapExpert(BaseExpert):
    """Tier 4 Specialist: Runs REAL sqlmap via ToolExecutor."""
    
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("SQLmap Specialist", llm_engine)
        self.system_prompt = "YOU ARE THE SQLMAP SPECIALIST. Detect and exploit SQL injection."

    def execute_task(self, task_instruction: str) -> str:
        logging.info(f"[SqlmapExpert] Real injection test: {task_instruction}")
        
        # Extract URL target
        urls = re.findall(r'https?://\S+', task_instruction)
        target = urls[0] if urls else task_instruction.strip()
        
        try:
            result = self.tools.run_sqlmap(target)
            
            if not result.success:
                return self.log_result(f"SQLMAP FAILED: {result.error}")
            
            if result.data.get("vulnerable"):
                injections = result.data.get("injections", [])
                output = f"SQLMAP: VULNERABLE to SQL Injection!\n  Target: {target}\n"
                for inj in injections:
                    output += f"  Parameter: {inj.get('parameter')} | Type: {inj.get('type')}\n"
                if result.data.get("database_type"):
                    output += f"  Database: {result.data['database_type']}\n"
                return self.log_result(output)
            else:
                return self.log_result(f"SQLMAP COMPLETE on {target}: No SQL injection found.")
                
        except Exception as e:
            return self.log_result(f"SQLMAP EXECUTION ERROR: {e}")
