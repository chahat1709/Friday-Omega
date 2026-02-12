import logging

class PolicyCompiler:
    """
    Deterministic safety engine (Non-LLM).
    Validates proposed actions before they hit the Hardware Abstraction Layer or Tool Executor.
    """
    def __init__(self, allowed_targets=None, allowed_tools=None):
        # Default ROE
        self.allowed_targets = allowed_targets or ["192.168.1.0/24", "127.0.0.1", "localhost", "10.0.0.0/8"]
        self.allowed_tools = allowed_tools or ["nmap", "ping", "whois", "shodan", "scan"]
        
    def validate_command(self, tool_name, target):
        """
        Checks if the tool and target are within the Rules of Engagement (ROE).
        Returns (True, "Reason") or (False, "Violation Reason")
        """
        # 1. Check Tool
        tool_clean = str(tool_name).lower().strip()
        if tool_clean not in self.allowed_tools:
            logging.warning(f"PolicyCompiler: Tool '{tool_name}' blocked. Not in allowlist.")
            return False, f"Tool '{tool_name}' is outside authorized scope."
            
        # 2. Check Target (Strict exact match or subnet check)
        target_clean = str(target).lower().strip()
        target_approved = False
        for allowed in self.allowed_targets:
            # Check for direct identity or cidr participation (simplified check for MVP)
            if target_clean == allowed.lower().strip():
                target_approved = True
                break
            # Optional: Add ipaddress.ip_network logic here for true CIDR validation
                
        if not target_approved:
            logging.warning(f"PolicyCompiler: Target '{target}' blocked. Out of ROE scope.")
            return False, f"Target '{target}' is not in authorized ROE scope."
            
        logging.info(f"PolicyCompiler: Command [{tool_name} -> {target}] passed scope check.")
        return True, "Scope Validation Passed."
