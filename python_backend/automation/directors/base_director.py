from abc import ABC, abstractmethod
import logging
import sys
import os
from typing import Dict, Any, List

# Standard path resolution for FRIDAY Omega
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.llm import LLMEngine
from core.blackboard import blackboard
from core.memory_rag import memory_rag

class BaseDirector(ABC):
    def __init__(self, domain_name: str, llm_engine: LLMEngine):
        self.domain = domain_name
        self.llm = llm_engine
        self.experts = {}
        logging.info(f"[{self.domain} Director] Initialized. Linked to Blackboard and Vector RAG Memory.")

    @abstractmethod
    def execute_mission(self, mission_instruction: str) -> str:
        return ""

    def share_finding(self, intel_type: str, data: Any, target: str = None):
        """Post intel to the global blackboard to cure Agent Amnesia."""
        blackboard.post_intel(
            agent_id=self.domain,
            intel_type=intel_type,
            data=data,
            confidence=100,
            target=target
        )
        
    def recall(self, query: str) -> str:
        """Search the collective RAG memory of all agents."""
        return memory_rag.search(query)

    def report_to_ceo(self, status: str, findings: List[str]):
        # Auto-share findings to Blackboard on exit
        for finding in findings:
            self.share_finding(intel_type="mission_finding", data=finding)
            
        return {"domain": self.domain, "status": status, "findings": findings}
