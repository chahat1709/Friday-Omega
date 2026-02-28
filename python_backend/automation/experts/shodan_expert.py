"""ShodanExpert — Real OSINT via Shodan API."""
import logging
import re
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.experts.base_expert import BaseExpert
from core.llm import LLMEngine

class ShodanExpert(BaseExpert):
    """Tier 4 Specialist: Runs REAL Shodan lookups."""
    
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Shodan Specialist", llm_engine)
        self.system_prompt = "YOU ARE THE SHODAN SPECIALIST. Map external attack surfaces."
        self.api_key = os.environ.get("SHODAN_API_KEY", "")

    def execute_task(self, task_instruction: str) -> str:
        logging.info(f"[ShodanExpert] Real OSINT: {task_instruction}")
        
        # Extract target IP
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', task_instruction)
        # Extract domain
        domains = re.findall(r'\b[a-zA-Z][\w\-]*\.[a-zA-Z]{2,}\b', task_instruction)
        
        target = ips[0] if ips else (domains[0] if domains else None)
        
        if not target:
            return self.log_result("SHODAN ERROR: No target IP or domain found in instruction.")
        
        if not self.api_key:
            # Fallback: use basic socket resolution
            try:
                import socket
                resolved_ip = socket.gethostbyname(target) if not ips else target
                return self.log_result(f"SHODAN (No API Key - DNS Fallback): {target} resolves to {resolved_ip}")
            except Exception as e:
                return self.log_result(f"SHODAN: DNS resolution failed for {target}: {e}")
        
        # Real Shodan API call
        try:
            import urllib.request
            url = f"https://api.shodan.io/shodan/host/{target}?key={self.api_key}"
            req = urllib.request.Request(url, headers={'User-Agent': 'FRIDAY-OSINT/1.0'})
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read().decode())
            
            output = f"SHODAN INTELLIGENCE on {target}:\n"
            output += f"  Organization: {data.get('org', 'Unknown')}\n"
            output += f"  ISP: {data.get('isp', 'Unknown')}\n"
            output += f"  Country: {data.get('country_name', 'Unknown')}\n"
            output += f"  Open Ports: {data.get('ports', [])}\n"
            
            vulns = data.get('vulns', [])
            if vulns:
                output += f"  ⚠️ Known Vulnerabilities: {', '.join(vulns[:10])}\n"
            
            return self.log_result(output)
            
        except Exception as e:
            return self.log_result(f"SHODAN API ERROR: {e}")
