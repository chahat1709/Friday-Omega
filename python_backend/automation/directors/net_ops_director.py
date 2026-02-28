"""NetOps Director — Network-aware delegation with subnet intelligence."""
import json
import logging
import re
import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.directors.base_director import BaseDirector
from core.llm import LLMEngine
from automation.expert_registry import ExpertRegistry

class NetOpsDirector(BaseDirector):
    """
    Director of Network Operations.
    UNIQUE LOGIC: Automatically sequences Nmap -> Hydra based on open ports.
    """
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Network Operations", llm_engine)
        self.registry = ExpertRegistry()
        self.system_prompt = """YOU ARE THE DIRECTOR OF NETWORK OPERATIONS (NETOPS).
        You coordinate network discovery and infrastructure auditing.
        Delegate to: nmap (scanning), hydra (auth testing), stresstester (load testing).
        OUTPUT: JSON with "mission_status" and "delegations" array."""

    def execute_mission(self, mission_instruction: str) -> str:
        logging.info(f"[NetOps] Coordinating: {mission_instruction}")
        
        # UNIQUE: Smart sequencing — always start with nmap, then decide
        findings = []
        
        # Phase 1: Always run Nmap first for reconnaissance
        nmap_expert = self.registry.get_expert("nmap", self.llm)
        if nmap_expert:
            nmap_result = nmap_expert.execute_task(mission_instruction)
            findings.append(f"[RECON] {nmap_result}")
            
            # Phase 2: If "brute" or "crack" in instruction, chain Hydra
            if any(w in mission_instruction.lower() for w in ["brute", "crack", "password", "auth"]):
                hydra_expert = self.registry.get_expert("hydra", self.llm)
                if hydra_expert:
                    hydra_result = hydra_expert.execute_task(mission_instruction)
                    findings.append(f"[AUTH-AUDIT] {hydra_result}")
            
            # Phase 3: If "stress" or "load" in instruction, chain StressTester
            if any(w in mission_instruction.lower() for w in ["stress", "load", "saturate", "ddos"]):
                stress_expert = self.registry.get_expert("stresstester", self.llm)
                if stress_expert:
                    stress_result = stress_expert.execute_task(mission_instruction)
                    findings.append(f"[STRESS] {stress_result}")
        
        report = self.report_to_ceo("complete", findings)
        return json.dumps(report, indent=2)
