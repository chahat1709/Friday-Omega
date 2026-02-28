"""NmapExpert — Real network scanning via ToolExecutor."""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.experts.base_expert import BaseExpert
from core.llm import LLMEngine

class NmapExpert(BaseExpert):
    """Tier 4 Specialist: Runs REAL nmap scans via ToolExecutor."""
    
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Nmap Scanner", llm_engine)
        self.system_prompt = "YOU ARE THE NMAP SPECIALIST. Generate precise nmap command flags for the given objective."

    def execute_task(self, task_instruction: str) -> str:
        logging.info(f"[NmapExpert] Real scan: {task_instruction}")
        
        # Use ToolExecutor to run real nmap
        # Parse target from instruction
        import re
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', task_instruction)
        target = ips[0] if ips else "127.0.0.1"
        
        # Determine scan type from instruction
        scan_type = "service"  # default
        t = task_instruction.lower()
        if "stealth" in t: scan_type = "stealth"
        elif "deep" in t or "full" in t: scan_type = "deep"
        elif "quick" in t or "fast" in t: scan_type = "quick"
        elif "vuln" in t: scan_type = "vuln"
        elif "udp" in t: scan_type = "udp"
        
        try:
            result = self.tools.run_nmap(target, scan_type=scan_type)
            
            if not result.success:
                return self.log_result(f"NMAP FAILED: {result.error}")
            
            # Build real output from parsed data
            hosts = result.data.get("hosts", [])
            output_lines = [f"NMAP {scan_type.upper()} SCAN on {target} (Duration: {result.duration:.1f}s)"]
            
            for host in hosts:
                open_ports = [p for p in host.get("ports", []) if p.get("state") == "open"]
                output_lines.append(f"  Found {len(open_ports)} open ports:")
                for p in open_ports:
                    output_lines.append(f"    {p['port']}/{p.get('protocol','tcp')} -> {p.get('service','unknown')} {p.get('version','')}")
            
            if not hosts:
                output_lines.append("  No hosts responded.")
            
            return self.log_result("\n".join(output_lines))
            
        except Exception as e:
            return self.log_result(f"NMAP EXECUTION ERROR: {e}")
