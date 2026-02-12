"""
Tool Executor Engine — Universal wrapper for all security tools.
Safely executes external CLI tools with timeout, logging, parsing, and error handling.

Every tool method:
1. Checks if the tool is installed
2. Builds the proper command
3. Executes with timeout
4. Parses structured output
5. Logs the execution for audit trail
6. Returns JSON-structured results for AI consumption
"""

import subprocess
import shutil
import json
import re
import logging
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("ToolExecutor")


class ToolResult:
    """Structured result from any tool execution."""
    
    def __init__(self, tool: str, success: bool, data: Any = None, 
                 raw_output: str = "", error: str = "", duration: float = 0):
        self.tool = tool
        self.success = success
        self.data = data or {}
        self.raw_output = raw_output
        self.error = error
        self.duration = duration
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "tool": self.tool,
            "success": self.success,
            "data": self.data,
            "raw_output": self.raw_output[:2000],  # Cap for AI context
            "error": self.error,
            "duration_seconds": round(self.duration, 2),
            "timestamp": self.timestamp
        }
    
    def __str__(self):
        if self.success:
            return f"[{self.tool}] Success ({self.duration:.1f}s)\n{json.dumps(self.data, indent=2)}"
        return f"[{self.tool}] Failed: {self.error}"


class ToolExecutor:
    """
    Executes real security tools and returns structured results.
    All tools are external CLI programs — this class wraps them safely.
    """
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.audit_log = []
        
        # Configure logging
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(log_dir, 'tool_executor.log'))
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
    
    def _load_config(self, config_path: str = None) -> dict:
        """Load tool paths from config."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _check_tool(self, tool_name: str) -> bool:
        """Check if a tool is installed and accessible."""
        return shutil.which(tool_name) is not None
    
    def _execute(self, cmd: List[str], timeout: int = 300, tool_name: str = "unknown") -> ToolResult:
        """Execute a command and return structured result."""
        
        # 1. EVASION: Mutate the command before execution
        from core.evasion_engine import evasion_engine
        import uuid
        
        evasion_engine.apply_jitter()
        stealth_cmd = evasion_engine.apply_evasion(cmd, tool_name)
        
        start_time = time.time()
        logger.info(f"Executing: {' '.join(stealth_cmd)}")
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "command": ' '.join(stealth_cmd)
        })
        
        try:
            result = subprocess.run(
                stealth_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            # 2. MEMORY RAG: Prevent context window collapse
            raw_data = result.stdout
            if len(raw_data) > 3000:
                from core.memory_rag import memory_rag
                rag_tag = f"RAG_STORE_{uuid.uuid4().hex[:6]}"
                rag_status = memory_rag.store(agent_id=tool_name, tool_name=tool_name, text=raw_data)
                raw_data = f"[OUTPUT TRUNCATED] Result exceeds 3000 chars. Stored in Vector Memory as {rag_tag}. Use search_memory('{tool_name} findings') to extract context. {rag_status}"
            
            if result.returncode == 0:
                return ToolResult(
                    tool=tool_name,
                    success=True,
                    raw_output=raw_data,
                    duration=duration
                )
            else:
                return ToolResult(
                    tool=tool_name,
                    success=False,
                    raw_output=result.stdout,
                    error=result.stderr or f"Exit code: {result.returncode}",
                    duration=duration
                )
                
        except FileNotFoundError:
            return ToolResult(
                tool=tool_name,
                success=False,
                error=f"Tool '{cmd[0]}' not installed. Install with: apt install {cmd[0]} (Kali/Linux)"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool=tool_name,
                success=False,
                error=f"Timeout after {timeout}s",
                duration=timeout
            )
        except Exception as e:
            return ToolResult(
                tool=tool_name,
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    # ==================== NETWORK RECON ====================
    
    def run_nmap(self, target: str, scan_type: str = "service", 
                 ports: str = None, scripts: str = None, 
                 timeout: int = 300) -> ToolResult:
        """
        Run Nmap with various scan types.
        
        scan_type options:
            - "quick"    : -T4 -F (fast, top 100 ports)
            - "service"  : -sV -T4 (service/version detection)
            - "deep"     : -sV -sC -O -T4 (version + scripts + OS)
            - "stealth"  : -sS -T2 (SYN stealth scan, slower)
            - "vuln"     : -sV --script vuln (vulnerability scripts)
            - "full"     : -sV -sC -O -p- -T4 (all ports, everything)
            - "udp"      : -sU -T4 (UDP scan)
        """
        if not self._check_tool("nmap"):
            return ToolResult(tool="nmap", success=False, 
                            error="Nmap not installed. Install: apt install nmap OR download from nmap.org")
        
        # Build command based on scan type
        cmd = ["nmap"]
        
        if scan_type == "quick":
            cmd.extend(["-T4", "-F"])
        elif scan_type == "service":
            cmd.extend(["-sV", "-T4"])
        elif scan_type == "deep":
            cmd.extend(["-sV", "-sC", "-O", "-T4"])
        elif scan_type == "stealth":
            cmd.extend(["-sS", "-T2"])
        elif scan_type == "vuln":
            cmd.extend(["-sV", "--script", "vuln"])
        elif scan_type == "full":
            cmd.extend(["-sV", "-sC", "-O", "-p-", "-T4"])
        elif scan_type == "udp":
            cmd.extend(["-sU", "-T4"])
        elif scan_type == "aggressive":
            cmd.extend(["-A", "-T4"])
        else:
            cmd.extend(["-sV", "-T4"])
        
        # Custom ports
        if ports:
            cmd.extend(["-p", ports])
        
        # Custom scripts
        if scripts:
            cmd.extend(["--script", scripts])
        
        # Output in XML for structured parsing
        cmd.extend(["-oX", "-", target])
        
        result = self._execute(cmd, timeout=timeout, tool_name="nmap")
        
        if result.success:
            result.data = self._parse_nmap_xml(result.raw_output)
        
        return result
    
    def _parse_nmap_xml(self, xml_output: str) -> dict:
        """Parse Nmap XML output into structured data."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_output)
            
            hosts = []
            for host_elem in root.findall('.//host'):
                host = {
                    "status": host_elem.find('status').get('state', 'unknown') if host_elem.find('status') is not None else 'unknown',
                    "addresses": [],
                    "hostnames": [],
                    "ports": [],
                    "os": []
                }
                
                # Addresses
                for addr in host_elem.findall('.//address'):
                    host["addresses"].append({
                        "addr": addr.get('addr'),
                        "type": addr.get('addrtype')
                    })
                
                # Hostnames
                for hostname in host_elem.findall('.//hostname'):
                    host["hostnames"].append(hostname.get('name', ''))
                
                # Ports
                for port_elem in host_elem.findall('.//port'):
                    port_data = {
                        "port": int(port_elem.get('portid', 0)),
                        "protocol": port_elem.get('protocol', 'tcp'),
                        "state": "unknown",
                        "service": "unknown",
                        "version": ""
                    }
                    
                    state = port_elem.find('state')
                    if state is not None:
                        port_data["state"] = state.get('state', 'unknown')
                    
                    service = port_elem.find('service')
                    if service is not None:
                        port_data["service"] = service.get('name', 'unknown')
                        product = service.get('product', '')
                        version = service.get('version', '')
                        port_data["version"] = f"{product} {version}".strip()
                    
                    # Scripts
                    scripts_output = []
                    for script in port_elem.findall('.//script'):
                        scripts_output.append({
                            "id": script.get('id'),
                            "output": script.get('output', '')[:500]
                        })
                    if scripts_output:
                        port_data["scripts"] = scripts_output
                    
                    host["ports"].append(port_data)
                
                # OS Detection
                for osmatch in host_elem.findall('.//osmatch'):
                    host["os"].append({
                        "name": osmatch.get('name', ''),
                        "accuracy": osmatch.get('accuracy', '0')
                    })
                
                hosts.append(host)
            
            return {
                "hosts": hosts,
                "total_hosts": len(hosts),
                "scan_info": {
                    "scanner": root.get('scanner', 'nmap'),
                    "args": root.get('args', ''),
                    "start_time": root.get('startstr', '')
                }
            }
        except Exception as e:
            logger.error(f"Nmap XML parse error: {e}")
            # Fallback: return raw text parsing
            return self._parse_nmap_text(xml_output)
    
    def _parse_nmap_text(self, output: str) -> dict:
        """Fallback text parsing for Nmap output."""
        open_ports = re.findall(r'(\d+)/(tcp|udp)\s+open\s+(\S+)\s*(.*?)(?:\n|$)', output)
        return {
            "hosts": [{
                "ports": [
                    {"port": int(p[0]), "protocol": p[1], "state": "open", 
                     "service": p[2], "version": p[3].strip()}
                    for p in open_ports
                ]
            }],
            "total_hosts": 1
        }
    
    # ==================== WEB APPLICATION ====================
    
    def run_nikto(self, target: str, port: int = 80, timeout: int = 300) -> ToolResult:
        """
        Run Nikto web server vulnerability scanner.
        Finds outdated software, dangerous files, misconfigurations.
        """
        if not self._check_tool("nikto"):
            return ToolResult(tool="nikto", success=False,
                            error="Nikto not installed. Install: apt install nikto")
        
        cmd = ["nikto", "-h", target, "-p", str(port), "-Format", "json", "-output", "-"]
        result = self._execute(cmd, timeout=timeout, tool_name="nikto")
        
        if result.success:
            try:
                result.data = json.loads(result.raw_output)
            except json.JSONDecodeError:
                # Parse text output
                vulnerabilities = re.findall(r'\+ (OSVDB-\d+|CVE-\d+-\d+)?:?\s*(.*)', result.raw_output)
                result.data = {
                    "vulnerabilities": [
                        {"id": v[0] or "INFO", "description": v[1].strip()}
                        for v in vulnerabilities if v[1].strip()
                    ]
                }
        
        return result
    
    def run_gobuster(self, target: str, mode: str = "dir", 
                     wordlist: str = "/usr/share/wordlists/dirb/common.txt",
                     timeout: int = 300) -> ToolResult:
        """
        Run Gobuster for directory/DNS/vhost bruteforcing.
        
        mode: "dir" (directories), "dns" (subdomains), "vhost" (virtual hosts)
        """
        if not self._check_tool("gobuster"):
            return ToolResult(tool="gobuster", success=False,
                            error="Gobuster not installed. Install: apt install gobuster")
        
        cmd = ["gobuster", mode, "-u", target, "-w", wordlist, "-q", "--no-color"]
        
        if mode == "dns":
            cmd = ["gobuster", "dns", "-d", target, "-w", wordlist, "-q", "--no-color"]
        
        result = self._execute(cmd, timeout=timeout, tool_name="gobuster")
        
        if result.success:
            found = []
            for line in result.raw_output.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('='):
                    # Parse: /path (Status: 200) [Size: 1234]
                    match = re.match(r'(\S+)\s+\(Status:\s*(\d+)\)\s*\[Size:\s*(\d+)\]', line)
                    if match:
                        found.append({
                            "path": match.group(1),
                            "status": int(match.group(2)),
                            "size": int(match.group(3))
                        })
                    else:
                        found.append({"path": line, "status": 0, "size": 0})
            
            result.data = {"found_paths": found, "count": len(found)}
        
        return result
    
    def run_sqlmap(self, target_url: str, data: str = None, 
                   level: int = 1, risk: int = 1,
                   timeout: int = 600) -> ToolResult:
        """
        Run SQLMap for SQL injection testing.
        
        target_url: URL with parameter (e.g., http://target.com/page?id=1)
        data: POST data (e.g., "username=test&password=test")
        level: 1-5 (higher = more tests)
        risk: 1-3 (higher = more aggressive)
        """
        if not self._check_tool("sqlmap"):
            return ToolResult(tool="sqlmap", success=False,
                            error="SQLMap not installed. Install: apt install sqlmap")
        
        cmd = ["sqlmap", "-u", target_url, "--batch", "--level", str(level), 
               "--risk", str(risk), "--output-dir=/tmp/sqlmap_output"]
        
        if data:
            cmd.extend(["--data", data])
        
        result = self._execute(cmd, timeout=timeout, tool_name="sqlmap")
        
        if result.success:
            injections = []
            # Parse SQLMap output for found injections
            vuln_patterns = re.findall(
                r'Parameter:\s+(\S+)\s+\((.*?)\)\s+.*?Type:\s+(.*?)(?:\n|Payload:)',
                result.raw_output, re.DOTALL
            )
            for param, place, vuln_type in vuln_patterns:
                injections.append({
                    "parameter": param,
                    "place": place,
                    "type": vuln_type.strip()
                })
            
            is_vulnerable = "is vulnerable" in result.raw_output.lower() or len(injections) > 0
            
            result.data = {
                "vulnerable": is_vulnerable,
                "injections": injections,
                "database_type": re.search(r'back-end DBMS:\s+(.*?)$', result.raw_output, re.MULTILINE),
            }
            if result.data["database_type"]:
                result.data["database_type"] = result.data["database_type"].group(1)
        
        return result
    
    # ==================== CREDENTIAL ATTACKS ====================
    
    def run_hydra(self, target: str, service: str = "ssh",
                  username: str = None, userlist: str = None,
                  password: str = None, passlist: str = None,
                  port: int = None, timeout: int = 600) -> ToolResult:
        """
        Run Hydra for online brute force attacks.
        
        service: ssh, ftp, telnet, http-get, http-post-form, mysql, rdp, etc.
        """
        if not self._check_tool("hydra"):
            return ToolResult(tool="hydra", success=False,
                            error="Hydra not installed. Install: apt install hydra")
        
        cmd = ["hydra"]
        
        if username:
            cmd.extend(["-l", username])
        elif userlist:
            cmd.extend(["-L", userlist])
        else:
            cmd.extend(["-l", "admin"])  # Default
        
        if password:
            cmd.extend(["-p", password])
        elif passlist:
            cmd.extend(["-P", passlist])
        else:
            # Default common passwords
            default_passlist = "/usr/share/wordlists/rockyou.txt"
            if os.path.exists(default_passlist):
                cmd.extend(["-P", default_passlist])
            else:
                return ToolResult(tool="hydra", success=False, 
                                error="No password list provided and default rockyou.txt not found")
        
        if port:
            cmd.extend(["-s", str(port)])
        
        cmd.extend(["-t", "4", "-f", target, service])
        
        result = self._execute(cmd, timeout=timeout, tool_name="hydra")
        
        if result.success:
            # Parse found credentials
            creds = re.findall(r'\[(\d+)\]\[(\S+)\]\s+host:\s+(\S+)\s+login:\s+(\S+)\s+password:\s+(\S+)',
                             result.raw_output)
            result.data = {
                "credentials_found": [
                    {"port": c[0], "service": c[1], "host": c[2], "login": c[3], "password": c[4]}
                    for c in creds
                ],
                "cracked": len(creds) > 0
            }
        
        return result
    
    def run_hashcat(self, hash_file: str, hash_type: int = 0,
                    wordlist: str = "/usr/share/wordlists/rockyou.txt",
                    timeout: int = 3600) -> ToolResult:
        """
        Run Hashcat for offline hash cracking.
        
        hash_type: 0=MD5, 100=SHA1, 1400=SHA256, 1000=NTLM, 1800=SHA512crypt, etc.
        """
        if not self._check_tool("hashcat"):
            return ToolResult(tool="hashcat", success=False,
                            error="Hashcat not installed. Install: apt install hashcat")
        
        cmd = ["hashcat", "-m", str(hash_type), "-a", "0", 
               hash_file, wordlist, "--force", "--quiet"]
        
        result = self._execute(cmd, timeout=timeout, tool_name="hashcat")
        
        if result.success:
            cracked = re.findall(r'(\S+):(\S+)', result.raw_output)
            result.data = {
                "cracked_hashes": [{"hash": c[0], "password": c[1]} for c in cracked],
                "count": len(cracked)
            }
        
        return result
    
    def run_john(self, hash_file: str, format: str = None,
                 wordlist: str = "/usr/share/wordlists/rockyou.txt",
                 timeout: int = 3600) -> ToolResult:
        """Run John the Ripper for password cracking."""
        if not self._check_tool("john"):
            return ToolResult(tool="john", success=False,
                            error="John the Ripper not installed. Install: apt install john")
        
        cmd = ["john", "--wordlist=" + wordlist]
        if format:
            cmd.append(f"--format={format}")
        cmd.append(hash_file)
        
        result = self._execute(cmd, timeout=timeout, tool_name="john")
        
        # Get cracked passwords
        show_result = self._execute(["john", "--show", hash_file], timeout=10, tool_name="john-show")
        if show_result.success:
            result.data = {"cracked": show_result.raw_output}
        
        return result
    
    # ==================== WIRELESS ====================
    
    def run_airmon(self, interface: str, action: str = "start") -> ToolResult:
        """Enable/disable monitor mode on WiFi interface."""
        if not self._check_tool("airmon-ng"):
            return ToolResult(tool="airmon-ng", success=False,
                            error="Aircrack-ng suite not installed. Install: apt install aircrack-ng")
        
        cmd = ["airmon-ng", action, interface]
        return self._execute(cmd, timeout=30, tool_name="airmon-ng")
    
    def run_airodump(self, interface: str, output_prefix: str = "/tmp/airodump",
                     channel: int = None, bssid: str = None,
                     timeout: int = 30) -> ToolResult:
        """
        Run airodump-ng for WiFi network discovery.
        Captures wireless traffic and lists access points.
        """
        if not self._check_tool("airodump-ng"):
            return ToolResult(tool="airodump-ng", success=False,
                            error="Aircrack-ng suite not installed. Install: apt install aircrack-ng")
        
        cmd = ["airodump-ng", "-w", output_prefix, "--output-format", "csv"]
        if channel:
            cmd.extend(["-c", str(channel)])
        if bssid:
            cmd.extend(["--bssid", bssid])
        cmd.append(interface)
        
        result = self._execute(cmd, timeout=timeout, tool_name="airodump-ng")
        
        # Parse CSV output
        csv_file = f"{output_prefix}-01.csv"
        if os.path.exists(csv_file):
            result.data = self._parse_airodump_csv(csv_file)
        
        return result
    
    def _parse_airodump_csv(self, csv_path: str) -> dict:
        """Parse airodump-ng CSV output."""
        networks = []
        clients = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            sections = content.split('\r\n\r\n')
            if len(sections) >= 1:
                # Parse APs
                lines = sections[0].strip().split('\n')
                for line in lines[2:]:  # Skip header
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 14:
                        networks.append({
                            "bssid": parts[0],
                            "channel": parts[3],
                            "power": parts[8],
                            "encryption": parts[5],
                            "cipher": parts[6],
                            "auth": parts[7],
                            "essid": parts[13]
                        })
        except Exception as e:
            logger.error(f"Airodump CSV parse error: {e}")
        
        return {"networks": networks, "clients": clients}
    
    def run_aircrack(self, capture_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt",
                     bssid: str = None, timeout: int = 3600) -> ToolResult:
        """Run aircrack-ng to crack WPA/WPA2 handshake."""
        if not self._check_tool("aircrack-ng"):
            return ToolResult(tool="aircrack-ng", success=False,
                            error="Aircrack-ng not installed. Install: apt install aircrack-ng")
        
        cmd = ["aircrack-ng", "-w", wordlist]
        if bssid:
            cmd.extend(["-b", bssid])
        cmd.append(capture_file)
        
        result = self._execute(cmd, timeout=timeout, tool_name="aircrack-ng")
        
        if result.success:
            key_match = re.search(r'KEY FOUND!\s*\[\s*(.*?)\s*\]', result.raw_output)
            result.data = {
                "cracked": key_match is not None,
                "key": key_match.group(1) if key_match else None
            }
        
        return result
    
    # ==================== ENUMERATION ====================
    
    def run_enum4linux(self, target: str, timeout: int = 120) -> ToolResult:
        """Run enum4linux for SMB/Windows enumeration."""
        if not self._check_tool("enum4linux"):
            return ToolResult(tool="enum4linux", success=False,
                            error="enum4linux not installed. Install: apt install enum4linux")
        
        cmd = ["enum4linux", "-a", target]
        result = self._execute(cmd, timeout=timeout, tool_name="enum4linux")
        
        if result.success:
            # Parse key findings
            users = re.findall(r'user:\[(.*?)\]', result.raw_output)
            shares = re.findall(r'Mapping:\s+(\S+)\s+Mapping:\s+(\S+)', result.raw_output)
            
            result.data = {
                "users": users,
                "shares": [{"name": s[0], "type": s[1]} for s in shares],
                "os_info": re.search(r'OS=\[(.*?)\]', result.raw_output)
            }
            if result.data["os_info"]:
                result.data["os_info"] = result.data["os_info"].group(1)
        
        return result
    
    def run_whatweb(self, target: str, timeout: int = 60) -> ToolResult:
        """Run WhatWeb for web fingerprinting."""
        if not self._check_tool("whatweb"):
            return ToolResult(tool="whatweb", success=False,
                            error="WhatWeb not installed. Install: apt install whatweb")
        
        cmd = ["whatweb", "--log-json=-", target]
        result = self._execute(cmd, timeout=timeout, tool_name="whatweb")
        
        if result.success:
            try:
                result.data = json.loads(result.raw_output)
            except json.JSONDecodeError:
                result.data = {"raw": result.raw_output}
        
        return result
    
    def run_wpscan(self, target: str, timeout: int = 300) -> ToolResult:
        """Run WPScan for WordPress vulnerability scanning."""
        if not self._check_tool("wpscan"):
            return ToolResult(tool="wpscan", success=False,
                            error="WPScan not installed. Install: apt install wpscan")
        
        cmd = ["wpscan", "--url", target, "--format", "json", "--no-banner"]
        result = self._execute(cmd, timeout=timeout, tool_name="wpscan")
        
        if result.success:
            try:
                result.data = json.loads(result.raw_output)
            except json.JSONDecodeError:
                result.data = {"raw": result.raw_output}
        
        return result
    
    # ==================== POST-EXPLOITATION ====================
    
    def run_responder(self, interface: str, timeout: int = 120) -> ToolResult:
        """Run Responder for LLMNR/NBT-NS poisoning."""
        if not self._check_tool("responder"):
            return ToolResult(tool="responder", success=False,
                            error="Responder not installed. Install: apt install responder")
        
        cmd = ["responder", "-I", interface, "-A"]  # -A for analyze mode (passive)
        return self._execute(cmd, timeout=timeout, tool_name="responder")
    
    # ==================== PACKET CAPTURE ====================
    
    def run_tshark(self, interface: str, capture_filter: str = None,
                   display_filter: str = None, count: int = 100,
                   timeout: int = 30) -> ToolResult:
        """Run tshark for packet capture and analysis."""
        if not self._check_tool("tshark"):
            return ToolResult(tool="tshark", success=False,
                            error="Tshark not installed. Install: apt install tshark (part of Wireshark)")
        
        cmd = ["tshark", "-i", interface, "-c", str(count)]
        if capture_filter:
            cmd.extend(["-f", capture_filter])
        if display_filter:
            cmd.extend(["-Y", display_filter])
        
        return self._execute(cmd, timeout=timeout, tool_name="tshark")
    
    # ==================== METASPLOIT ====================
    
    def run_metasploit(self, module: str, options: Dict[str, str] = None,
                       timeout: int = 600) -> ToolResult:
        """
        Run a Metasploit module via msfrpc or msfconsole resource script.
        
        module: e.g., "exploit/multi/http/apache_normalize_path_rce"
        options: e.g., {"RHOSTS": "192.168.1.100", "LHOST": "192.168.1.50"}
        """
        # Method 1: Try pymetasploit3 RPC
        try:
            from pymetasploit3.msfrpc import MsfRpcClient
            
            msf_config = self.config.get('tools', {}).get('metasploit_rpc', {})
            host = msf_config.get('host', '127.0.0.1')
            port = msf_config.get('port', 55553)
            password = msf_config.get('password', 'msf')
            
            client = MsfRpcClient(password, server=host, port=port)
            
            # Create console
            console = client.consoles.console()
            
            # Send commands
            console.write(f"use {module}\n")
            time.sleep(1)
            
            if options:
                for key, value in options.items():
                    console.write(f"set {key} {value}\n")
                    time.sleep(0.5)
            
            console.write("run\n")
            time.sleep(5)
            
            output = console.read()
            console.destroy()
            
            return ToolResult(
                tool="metasploit",
                success=True,
                raw_output=output.get('data', ''),
                data={"method": "rpc", "module": module, "options": options}
            )
            
        except ImportError:
            logger.info("pymetasploit3 not installed, falling back to resource script")
        except Exception as e:
            logger.warning(f"MSF RPC failed: {e}, falling back to resource script")
        
        # Method 2: Fallback to msfconsole resource script
        if not self._check_tool("msfconsole"):
            return ToolResult(tool="metasploit", success=False,
                            error="Metasploit not installed. Install: apt install metasploit-framework\n"
                                  "For RPC: pip install pymetasploit3 && msfrpcd -P msf")
        
        # Create resource script
        rc_path = "/tmp/friday_msf.rc"
        with open(rc_path, 'w') as f:
            f.write(f"use {module}\n")
            if options:
                for key, value in options.items():
                    f.write(f"set {key} {value}\n")
            f.write("run\n")
            f.write("exit\n")
        
        cmd = ["msfconsole", "-q", "-r", rc_path]
        result = self._execute(cmd, timeout=timeout, tool_name="metasploit")
        
        # Cleanup
        try:
            os.remove(rc_path)
        except:
            pass
        
        if result.success:
            result.data = {"method": "resource_script", "module": module, "options": options}
        
        return result
    
    def run_msfvenom(self, payload: str, format: str = "raw",
                     lhost: str = None, lport: int = 4444,
                     output_file: str = None) -> ToolResult:
        """Generate Metasploit payloads."""
        if not self._check_tool("msfvenom"):
            return ToolResult(tool="msfvenom", success=False,
                            error="Metasploit not installed")
        
        cmd = ["msfvenom", "-p", payload, "-f", format]
        if lhost:
            cmd.append(f"LHOST={lhost}")
        cmd.append(f"LPORT={lport}")
        
        if output_file:
            cmd.extend(["-o", output_file])
        
        return self._execute(cmd, timeout=120, tool_name="msfvenom")
    
    # ==================== UTILITY ====================
    
    def check_available_tools(self) -> Dict[str, bool]:
        """Check which security tools are installed."""
        tools = [
            "nmap", "nikto", "gobuster", "sqlmap", "hydra", "hashcat", "john",
            "aircrack-ng", "airodump-ng", "airmon-ng", "aireplay-ng",
            "enum4linux", "whatweb", "wpscan", "responder", "tshark",
            "msfconsole", "msfvenom", "netcat", "masscan"
        ]
        
        availability = {}
        for tool in tools:
            availability[tool] = self._check_tool(tool)
        
        return availability
    
    def get_audit_log(self) -> List[dict]:
        """Return the audit trail of all executed commands."""
        return self.audit_log
