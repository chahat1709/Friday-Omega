"""IntelOps Director — OSINT-focused with enrichment pipeline."""
import json
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.directors.base_director import BaseDirector
from core.llm import LLMEngine
from automation.expert_registry import ExpertRegistry

class IntelOpsDirector(BaseDirector):
    """
    Director of Intelligence Operations.
    UNIQUE LOGIC: Runs multi-source OSINT enrichment pipeline.
    """
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Intelligence Operations", llm_engine)
        self.registry = ExpertRegistry()
        self.system_prompt = """YOU ARE THE DIRECTOR OF INTELLIGENCE OPERATIONS (INTELOPS).
        You transform raw data into actionable intelligence.
        Run multi-source OSINT enrichment on targets.
        Delegate to: shodan (infrastructure), nmap (ports)."""

    def execute_mission(self, mission_instruction: str) -> str:
        logging.info(f"[IntelOps] Intelligence gathering: {mission_instruction}")
        
        findings = []
        
        # UNIQUE: Intelligence enrichment pipeline
        # Phase 1: External intelligence via Shodan
        shodan = self.registry.get_expert("shodan", self.llm)
        if shodan:
            findings.append(f"[SIGINT] {shodan.execute_task(mission_instruction)}")
        
        # Phase 2: Active probing via Nmap (if target is in scope)
        import re
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', mission_instruction)
        if ips:
            nmap = self.registry.get_expert("nmap", self.llm)
            if nmap:
                findings.append(f"[ACTIVE-PROBE] {nmap.execute_task(mission_instruction)}")
        
        # Phase 3: AI Analysis — synthesize intelligence into a brief
        if self.llm and findings:
            try:
                analysis = self.llm.generate(
                    system_prompt="You are an intelligence analyst. Synthesize raw data into a threat brief.",
                    prompt=f"Raw intelligence:\n{chr(10).join(findings)}\n\nProvide a 3-line threat assessment."
                )
                findings.append(f"[THREAT-BRIEF] {analysis}")
            except Exception:
                pass
        
        report = self.report_to_ceo("complete", findings)
        return json.dumps(report, indent=2)
