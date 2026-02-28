from abc import ABC, abstractmethod
import logging
import sys
import os
from typing import Dict, Any

# Standard path resolution for FRIDAY Omega
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.llm import LLMEngine
from core.tool_executor import ToolExecutor

class BaseExpert(ABC):
    def __init__(self, expert_name: str, llm_engine: LLMEngine):
        self.name = expert_name
        self.llm = llm_engine
        self.tools = ToolExecutor()
        self.system_prompt = ""

    @abstractmethod
    def execute_task(self, task_instruction: str) -> str:
        return ""

    def log_result(self, result: str):
        logging.info(f"[{self.name}] Result: {str(result)[:50]}...")
        return result
