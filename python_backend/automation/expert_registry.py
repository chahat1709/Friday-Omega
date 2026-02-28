import json
import logging
import os
import sys
from typing import Dict, Any, Optional

# Standard path resolution for FRIDAY Omega
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.experts.nmap_expert import NmapExpert
from automation.experts.hydra_expert import HydraExpert
from automation.experts.stress_tester import StressTesterExpert
from automation.experts.flipper_expert import FlipperExpert
from automation.experts.metasploit_expert import MetasploitExpert
from automation.experts.sqlmap_expert import SqlmapExpert
from automation.experts.shodan_expert import ShodanExpert
from automation.experts.dynamic_expert import DynamicExpert

class ExpertRegistry:
    def __init__(self, registry_file: str = "expert_registry.json"):
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        self.registry_path = os.path.join(config_dir, registry_file)
        self.active_experts = {}
        self.catalog = {}
        self._load_catalog()

    def _load_catalog(self):
        """Loads the full JSON catalog of 1000 agents."""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.catalog = json.load(f)
                logging.info(f"[Registry] Loaded {len(self.catalog)} agent profiles from catalog.")
            except Exception as e:
                logging.error(f"[Registry] Failed to parse {self.registry_path}: {e}")
        else:
            logging.warning(f"[Registry] Catalog {self.registry_path} not found. Please run scripts/generate_1000_agents.py.")

    def get_expert(self, expert_id: str, llm_engine):
        """
        Lazily loads an expert. Checks hardcoded Elite 7 first, 
        then searches the 1000-agent catalog.
        """
        expert_id = expert_id.lower()
        
        # 1. Check if already instantiated
        if expert_id in self.active_experts:
            return self.active_experts[expert_id]
        
        # 2. Check Elite 7 Hardcoded Classes
        elite_map = {
            "nmap": NmapExpert,
            "hydra": HydraExpert,
            "stresstester": StressTesterExpert,
            "flipper": FlipperExpert,
            "metasploit": MetasploitExpert,
            "sqlmap": SqlmapExpert,
            "shodan": ShodanExpert
        }
        
        if expert_id in elite_map:
            logging.info(f"[Registry] Summoning Elite Expert: {expert_id}")
            expert_instance = elite_map[expert_id](llm_engine)
            self.active_experts[expert_id] = expert_instance
            return expert_instance
            
        # 3. Check 1000-Agent Catalog
        # First check exact ID (EXP-0001) or specific name match
        for key, profile in self.catalog.items():
            if expert_id == key.lower() or expert_id == profile.get("id", "").lower() or expert_id == profile.get("tool", "").lower():
                logging.info(f"[Registry] Summoning Catalog Expert: {profile['id']} ({profile['name']})")
                expert_instance = DynamicExpert(profile['id'], profile, llm_engine)
                # Store by the requested ID for fast lookup next time
                self.active_experts[expert_id] = expert_instance
                return expert_instance
                
        # 4. Fallback search (find any agent matching the requested tool)
        for key, profile in self.catalog.items():
            if expert_id in key.lower() or expert_id in profile.get("description", "").lower():
                logging.info(f"[Registry] Summoning Fallback Catalog Expert: {profile['id']} ({profile['name']})")
                expert_instance = DynamicExpert(profile['id'], profile, llm_engine)
                self.active_experts[expert_id] = expert_instance
                return expert_instance

        logging.warning(f"[Registry] Expert '{expert_id}' not found in Elite 7 or 1000-Agent Catalog.")
        return None

    def get_catalog_size(self):
        return len(self.catalog)

registry = ExpertRegistry()
