"""AppSec Director — Web security focused with SQLi/XSS awareness."""
import json
import logging
import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.directors.base_director import BaseDirector
from core.llm import LLMEngine
from automation.expert_registry import ExpertRegistry

class AppSecDirector(BaseDirector):
    """
    Director of Application Security.
    UNIQUE LOGIC: Runs SQLmap for injection, delegates web-specific tasks.
    """
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Application Security", llm_engine)
        self.registry = ExpertRegistry()
        self.system_prompt = """YOU ARE THE DIRECTOR OF APPLICATION SECURITY (APPSEC).
        You focus on web applications, APIs, and database security.
        Delegate to: sqlmap (injection), shodan (external footprint).
        OUTPUT: JSON with "mission_status" and "delegations" array."""

    def execute_mission(self, mission_instruction: str) -> str:
        logging.info(f"[AppSec] Coordinating: {mission_instruction}")
        
        findings = []
        t = mission_instruction.lower()
        
        # UNIQUE: Web-specific attack chain
        # Phase 1: External footprint
        if any(w in t for w in ["footprint", "external", "surface", "shodan"]):
            shodan = self.registry.get_expert("shodan", self.llm)
            if shodan:
                findings.append(f"[FOOTPRINT] {shodan.execute_task(mission_instruction)}")
        
        # Phase 2: SQL Injection testing (always for web targets)
        if any(w in t for w in ["sql", "inject", "database", "web", "app", "url"]):
            sqlmap = self.registry.get_expert("sqlmap", self.llm)
            if sqlmap:
                findings.append(f"[INJECTION] {sqlmap.execute_task(mission_instruction)}")
        
        # Phase 3: Exploitation if vulnerabilities found
        if any(w in t for w in ["exploit", "msf", "metasploit", "pwn"]):
            msf = self.registry.get_expert("metasploit", self.llm)
            if msf:
                findings.append(f"[EXPLOIT] {msf.execute_task(mission_instruction)}")
        
        if not findings:
            # Default: run shodan + sqlmap
            shodan = self.registry.get_expert("shodan", self.llm)
            if shodan: findings.append(f"[FOOTPRINT] {shodan.execute_task(mission_instruction)}")
        
        report = self.report_to_ceo("complete", findings)
        return json.dumps(report, indent=2)
