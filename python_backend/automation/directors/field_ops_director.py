"""FieldOps Director — Physical proximity and hardware-focused."""
import json
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.directors.base_director import BaseDirector
from core.llm import LLMEngine
from automation.expert_registry import ExpertRegistry
from core.hardware_bridge import hardware_bridge

class FieldOpsDirector(BaseDirector):
    """
    Director of Field Operations.
    UNIQUE LOGIC: Checks hardware status before delegating physical missions.
    """
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Field Operations", llm_engine)
        self.registry = ExpertRegistry()
        self.bridge = hardware_bridge
        self.system_prompt = """YOU ARE THE DIRECTOR OF FIELD OPERATIONS (FIELDOPS).
        You coordinate physical breaches requiring hardware (Flipper, Proxmark, Serial).
        ALWAYS check hardware status before delegating.
        Delegate to: flipper (RFID/Sub-GHz/NFC/IR)."""

    def execute_mission(self, mission_instruction: str) -> str:
        logging.info(f"[FieldOps] Physical mission: {mission_instruction}")
        
        findings = []
        
        # UNIQUE: Hardware status check first
        hw_status = self.bridge.get_status()
        if hw_status["mode"] == "simulator":
            findings.append(f"[HW-STATUS] Running in SIMULATOR mode. No physical hardware connected.")
        else:
            findings.append(f"[HW-STATUS] REAL mode. {hw_status['device_count']} device(s) connected: {list(hw_status['devices'].keys())}")
        
        # Phase 1: Delegate to Flipper specialist
        flipper = self.registry.get_expert("flipper", self.llm)
        if flipper:
            result = flipper.execute_task(mission_instruction)
            findings.append(f"[FLIPPER] {result}")
        
        report = self.report_to_ceo("complete", findings)
        return json.dumps(report, indent=2)
