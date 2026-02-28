"""
FRIDAY Omega — Multi-Agent System (CEO/Supervisor)
The strategic brain that coordinates ALL agents via LLM-driven routing.

Architecture:
  - 11 Original Agents (Blind, Vision, Mobile, IoT, Pentest, BugHunter, Coder, DeepAudit, OSINT, Workflow)
  - 4 Domain Directors (NetOps, AppSec, IntelOps, FieldOps)
  - Expert Registry (7 Specialists via lazy loading)
  - Security Gates (PlanValidator, AuditLogger)
"""

import json
import re
import time
import sys
import os
import logging

# Standard path resolution for FRIDAY Omega
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLMEngine
from automation.humanoid_agent import HumanoidAgent
from automation.blind_executor import BlindExecutor
from automation.mobile_agent import MobileAgent
from automation.iot_agent import IoTAgent
from automation.pentest_agent import PentestAgent
from automation.bug_hunter_agent import BugHunterAgent
from automation.coder_agent import CoderAgent
from automation.deep_audit_agent import DeepAuditAgent
from automation.osint_agent import OSINTAgent
from core.workflow_engine import PentestWorkflow
from core.plan_validator import PlanValidator
from core.audit_logger import AuditLogger
from core.hardware_bridge import HardwareBridge

# C-Suite Directors
from automation.directors.net_ops_director import NetOpsDirector
from automation.directors.app_sec_director import AppSecDirector
from automation.directors.intel_ops_director import IntelOpsDirector
from automation.directors.field_ops_director import FieldOpsDirector


class MultiAgentSystem:
    """
    The CEO of FRIDAY Omega.
    Routes requests to the correct agent using LLM-driven strategic analysis.
    Integrates C-Suite Directors for domain-level coordination.
    """
    def __init__(self, llm_engine: LLMEngine, humanoid_agent: HumanoidAgent):
        self.llm = llm_engine
        self.worker = humanoid_agent
        
        # ── Security & Infrastructure ──
        self.validator = PlanValidator(llm_engine)
        self.audit = AuditLogger()
        self.hardware = HardwareBridge(mode="simulator")
        
        # ── Original 11 Agents (Real operational code) ──
        self.blind = BlindExecutor()
        self.mobile = MobileAgent(llm_engine)
        self.iot = IoTAgent()
        self.pentest = PentestAgent(llm_engine)
        self.bug_hunter = BugHunterAgent(llm_engine)
        self.coder = CoderAgent(llm_engine)
        self.deep_audit = DeepAuditAgent(mobile_agent=self.mobile, pentest_agent=self.pentest)
        self.osint = OSINTAgent(llm_engine)
        self.workflow = PentestWorkflow(llm_engine)
        
        # ── C-Suite Directors (Hierarchical delegation layer) ──
        self.net_ops = NetOpsDirector(llm_engine)
        self.app_sec = AppSecDirector(llm_engine)
        self.intel_ops = IntelOpsDirector(llm_engine)
        self.field_ops = FieldOpsDirector(llm_engine)
        
        # Load Supervisor Prompt
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prompts', 'supervisor.md')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.supervisor_prompt = f.read()
        except FileNotFoundError:
            logging.warning(f"Supervisor prompt not found at {prompt_path}")
            self.supervisor_prompt = "You are the SUPERVISOR. Route requests to the correct agent. Output JSON with target_agent and instruction."
        
        # Log available tools
        available_count = sum(1 for v in self.pentest.available_tools.values() if v)
        print(f"[MultiAgent] Agents loaded: Pentest, BugHunter, IoT, Mobile, Coder, DeepAudit, OSINT, Workflow")
        print(f"[MultiAgent] Directors loaded: NetOps, AppSec, IntelOps, FieldOps")
        print(f"[MultiAgent] Pentest tools: {available_count}/{len(self.pentest.available_tools)} available")

    def process_request(self, user_input: str) -> str:
        """
        Main entry point. Uses LLM to decide which agent handles the request.
        Falls back to keyword matching if LLM routing fails.
        """
        print(f"[Supervisor] Analyzing request: '{user_input}'")
        
        # ── Step 1: LLM-Driven Strategic Routing ──
        target_agent = None
        instruction = user_input
        
        try:
            routing_response = self.llm.generate(
                system_prompt=self.supervisor_prompt,
                prompt=user_input,
                temperature=0.1
            )
            
            # Parse JSON from LLM response
            json_match = re.search(r'\{[^{}]*\}', routing_response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                target_agent = decision.get("target_agent", "").upper()
                instruction = decision.get("instruction", user_input)
                thought = decision.get("thought", "")
                logging.info(f"[Supervisor] Thought: {thought}")
                logging.info(f"[Supervisor] Route -> {target_agent}")
        except Exception as e:
            logging.warning(f"[Supervisor] LLM routing failed: {e}. Falling back to keyword matching.")
        
        # ── Step 2: Fallback Keyword Routing (if LLM fails) ──
        if not target_agent:
            target_agent = self._keyword_route(user_input)
            logging.info(f"[Supervisor] Keyword fallback -> {target_agent}")
        
        # ── Step 3: Audit Log ──
        self.audit.log_action("SYSTEM", "Supervisor", "route", target_agent, f"Routing: {user_input[:50]}")
        
        # ── Step 4: Execute via Target Agent ──
        try:
            return self._dispatch(target_agent, instruction)
        except Exception as e:
            logging.error(f"[Supervisor] Dispatch error: {e}")
            return f"Error executing request: {e}"

    def _keyword_route(self, text: str) -> str:
        """Deterministic keyword-based routing fallback."""
        t = text.lower()
        
        # Priority order matches supervisor.md
        if any(w in t for w in ["on my phone", "mobile", "android", "whatsapp"]):
            return "MOBILE_WORKER"
        if any(w in t for w in ["full audit", "full pentest", "automated audit", "full scan"]):
            return "WORKFLOW"
        if any(w in t for w in ["pentest", "nmap", "scan ", "vuln", "metasploit", "sqlmap", "nikto",
                                "gobuster", "hydra", "enumerate", "wpscan", "exploit", "authorize"]):
            return "PENTEST_AGENT"
        if any(w in t for w in ["shodan", "whois", "dns recon", "virustotal", "exploit search",
                                "breach check", "osint", "recon"]):
            return "OSINT_AGENT"
        if any(w in t for w in ["bug hunt", "hunt ", "find bugs", "test website"]):
            return "BUG_HUNTER"
        if any(w in t for w in ["deep audit", "security audit", "check my phone", "wifi security", "smb check"]):
            return "DEEP_AUDIT"
        if any(w in t for w in ["scan network", "arp scan", "port scan", "check ports", "discover devices"]):
            return "IOT_AGENT"
        if any(w in t for w in ["write code", "create code", "debug", "explain code", "refactor"]):
            return "CODER"
        if any(w in t for w in ["flipper", "rfid", "clone badge", "sub-ghz", "hardware", "physical"]):
            return "FIELD_OPS"
        if any(w in t for w in ["open ", "launch ", "minimize", "close "]):
            return "BLIND_EXECUTOR"
        
        return "VISION_WORKER"

    def _dispatch(self, target_agent: str, instruction: str) -> str:
        """Routes to the correct agent and returns their output."""
        
        # ── Original Agents ──
        if target_agent == "BLIND_EXECUTOR":
            return self.blind.execute(instruction)
        
        elif target_agent == "VISION_WORKER":
            return self.worker.solve_task(instruction)
        
        elif target_agent == "MOBILE_WORKER":
            return self.mobile.execute(instruction)
        
        elif target_agent == "IOT_AGENT":
            return self.iot.execute(instruction)
        
        elif target_agent == "PENTEST_AGENT":
            return self.pentest.execute(instruction)
        
        elif target_agent == "BUG_HUNTER":
            return self.bug_hunter.execute(instruction)
        
        elif target_agent == "CODER":
            return self.coder.execute(instruction)
        
        elif target_agent == "DEEP_AUDIT":
            return self.deep_audit.execute(instruction)
        
        elif target_agent in ("OSINT_AGENT", "OSINT"):
            return self.osint.execute(instruction)
        
        elif target_agent == "WORKFLOW":
            return self.workflow.run_full_audit(instruction)
        
        # ── C-Suite Directors ──
        elif target_agent == "NET_OPS":
            return self.net_ops.execute_mission(instruction)
        
        elif target_agent == "APP_SEC":
            return self.app_sec.execute_mission(instruction)
        
        elif target_agent in ("INTEL_OPS",):
            return self.intel_ops.execute_mission(instruction)
        
        elif target_agent in ("FIELD_OPS", "HARDWARE"):
            return self.field_ops.execute_mission(instruction)
        
        else:
            # Unknown agent — try general LLM response
            logging.warning(f"[Supervisor] Unknown agent: {target_agent}. Using LLM fallback.")
            return self.llm.generate(
                system_prompt="You are FRIDAY, a helpful AI assistant.",
                prompt=instruction
            )

    def get_available_agents(self) -> list:
        """Returns list of all available agent types for frontend display."""
        agents = [
            "BLIND_EXECUTOR", "VISION_WORKER", "MOBILE_WORKER", "IOT_AGENT",
            "PENTEST_AGENT", "BUG_HUNTER", "CODER", "DEEP_AUDIT", "OSINT_AGENT",
            "WORKFLOW", "NET_OPS", "APP_SEC", "INTEL_OPS", "FIELD_OPS"
        ]
        return agents
