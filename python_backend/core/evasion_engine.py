import random
import time
import logging

class EvasionEngine:
    """
    Tactical obfuscation layer. 
    Defeats elementary WAFs and static rule sets by mutating payloads,
    user-agents, proxies, and execution timing.
    """
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
        ]
        
    def get_random_ua(self) -> str:
        return random.choice(self.user_agents)

    def apply_evasion(self, cmd_list: list, tool_name: str) -> list:
        """Injects evasion flags based on the underlying tool."""
        evaded_cmd = cmd_list.copy()
        
        if tool_name == "sqlmap":
            if "--random-agent" not in evaded_cmd:
                evaded_cmd.append("--random-agent")
            if "--delay" not in str(evaded_cmd):
                evaded_cmd.extend(["--delay", str(random.uniform(0.5, 1.5))])
                
        elif tool_name == "nmap":
            # Avoid aggressive timing templates if stealth is requested implicitly
            if not any(arg.startswith("-T") for arg in evaded_cmd):
                evaded_cmd.append("-T2") # Polite
            if "--randomize-hosts" not in evaded_cmd:
                evaded_cmd.append("--randomize-hosts")
                
        elif tool_name in ["gobuster", "ffuf", "nikto"]:
            user_agent = self.get_random_ua()
            if tool_name == "gobuster":
                evaded_cmd.extend(["-a", user_agent])
            elif tool_name == "ffuf":
                evaded_cmd.extend(["-H", f"User-Agent: {user_agent}"])
            elif tool_name == "nikto":
                evaded_cmd.extend(["-useragent", user_agent])

        logging.info(f"[EvasionEngine] Obfuscated payload generated for {tool_name}")
        return evaded_cmd

    def apply_jitter(self, min_ms: int = 500, max_ms: int = 2000):
        """Pauses thread execution to defeat rate-limiters based on rigid patterns."""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        logging.debug(f"[EvasionEngine] Jitter pause: {delay:.2f}s")
        time.sleep(delay)

evasion_engine = EvasionEngine()
