import logging
import sys
import os
from automation.experts.base_expert import BaseExpert
from core.llm import LLMEngine
from core.hardware_bridge import hardware_bridge

# Standard path resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class FlipperExpert(BaseExpert):
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Flipper Specialist", llm_engine)
        self.bridge = hardware_bridge
        self.system_prompt = """
        YOU ARE THE FLIPPER SPECIALIST.
        You manipulate the physical world via Sub-GHz, NFC, RFID, and IR.
        Use the hardware bridge to send commands.
        """

    def execute_task(self, task_instruction: str) -> str:
        logging.info(f"[FlipperExpert] Physical Task: {task_instruction}")
        # Routing to hardware bridge
        result = self.bridge.send_command("flipper_zero", task_instruction)
        return self.log_result(result)
