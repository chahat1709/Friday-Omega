import socket
import subprocess
import threading
import time
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

class IoTAgent:
    """
    Controls Smart Devices and Scans the Network.
    Capabilities:
    1. Network Scanner (ARP/Ping)
    2. Port Scanner ("Hacker Mode")
    3. Wake-on-LAN
    4. Smart Device Control (Placeholders for Tuya/Kasa)
    """
    def __init__(self):
        self.local_ip = self._get_local_ip()
        self.network_prefix = ".".join(self.local_ip.split(".")[:3]) + "."
        self.logger = logging.getLogger(__name__)

    def _get_local_ip(self):
        try:
            # Try internet connection method first
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            # Fallback: Work offline
            try:
                return socket.gethostbyname(socket.gethostname())
            except:
                return "127.0.0.1"

    def execute(self, instruction):
        """
        Parses high-level IoT instructions.
        """
        instruction = instruction.lower()
        print(f"[IoTAgent] Executing: {instruction}")

        if "scan" in instruction and "arp" not in instruction:
            return self._scan_network()

        if "arp" in instruction or "discover" in instruction:
            return self._arp_scan()

        if "hack" in instruction or "check ports" in instruction:
            # Extract target IP if provided, else scan self or gateway
            target = "127.0.0.1" 
             # Simple regex for IP
            import re
            ips = re.findall(r'[0-9]+(?:\.[0-9]+){3}', instruction)
            if ips: target = ips[0]
            
            return self._scan_ports(target, ports="full" if "full" in instruction else "common")

        if "turn on" in instruction or "turn off" in instruction:
            return (
                "⚠️ Smart device control requires local API integration.\n"
                "Supported protocols (when configured):\n"
                "  • Tuya Smart (pip install tinytuya)\n"
                "  • TP-Link Kasa (pip install python-kasa)\n"
                "  • Shelly (HTTP REST API)\n"
                "  • MQTT (pip install paho-mqtt)\n\n"
                "Configure device credentials in config.json under 'iot_integrations'."
            )

        return ("IoT Agent Commands:\n"
                "• 'Scan network' — Ping sweep (all 255 hosts)\n"
                "• 'ARP discover' — ARP scan for MAC addresses\n"
                "• 'Check ports [IP]' — Port scan target\n"
                "• 'Check ports [IP] full' — Full 65535 port scan")

    def _arp_scan(self):
        """
        ARP scan using Scapy — discovers devices with MAC addresses.
        More reliable than ping sweep, finds devices that block ICMP.
        """
        try:
            from scapy.all import ARP, Ether, srp
            
            target_range = self.network_prefix + "0/24"
            print(f"[IoTAgent] ARP scanning {target_range}...")
            
            # Build ARP request
            arp = ARP(pdst=target_range)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp
            
            # Send and receive
            result = srp(packet, timeout=3, verbose=0)[0]
            
            devices = []
            for sent, received in result:
                devices.append({
                    "ip": received.psrc,
                    "mac": received.hwsrc
                })
            
            if not devices:
                return "ARP scan complete. No devices found."
            
            output = [f"📡 ARP Scan — {target_range}"]
            output.append(f"   Found: {len(devices)} devices\n")
            output.append(f"   {'IP':<18}{'MAC':<20}")
            output.append(f"   {'─'*38}")
            for d in devices:
                output.append(f"   {d['ip']:<18}{d['mac']:<20}")
            
            return "\n".join(output)
            
        except ImportError:
            return ("❌ Scapy not installed for ARP scanning.\n"
                    "Install: pip install scapy\n"
                    "Falling back to ping sweep...\n\n" + self._scan_network())
        except PermissionError:
            return ("❌ ARP scan requires root/admin privileges.\n"
                    "Run with: sudo python main.py\n"
                    "Falling back to ping sweep...\n\n" + self._scan_network())
        except Exception as e:
            return f"❌ ARP scan error: {e}\nFalling back to ping sweep...\n\n" + self._scan_network()

    def _scan_network(self):
        """
        Basic Ping Sweep (Fast).
        """
        print(f"[IoTAgent] Scanning {self.network_prefix}0/24 ...")
        active_hosts = []
        
        # Full subnet scan (1-255)
        targets = [f"{self.network_prefix}{i}" for i in range(1, 256)]
        
        def ping_host(ip):
            param = '-n' if platform.system().lower()=='windows' else '-c'
            command = ['ping', param, '1', '-w' if platform.system().lower()=='windows' else '-W', '1', ip]
            try:
                if subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2) == 0:
                    return ip
            except:
                pass
            return None

        # Use ThreadPoolExecutor with limited workers
        active_hosts = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(ping_host, ip): ip for ip in targets}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    active_hosts.append(result)
                    print(f"  Found: {result}")

        return f"Network Scan Complete. Active Devices found: {', '.join(active_hosts)}"

    def _scan_ports(self, ip, ports="common"):
        """
        Scans ports on target IP. 
        ports: "common" (top 24), "full" (1-65535), or list of ints
        """
        # Input validation
        if not self._is_valid_ip(ip):
            return f"Error: Invalid IP address '{ip}'"

        print(f"[IoTAgent] Port Scanning {ip} ({ports})...")
        
        target_ports = []
        if ports == "full":
            target_ports = range(1, 65536)
        elif isinstance(ports, list):
            target_ports = ports
        else:
            # Comprehensive port list (top 100 most common)
            target_ports = [
                20, 21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 
                995, 1723, 3306, 3389, 5432, 5900, 8080, 8443, 27017
            ]
        
        # Dictionary for common service names (for reporting)
        common_ports = {
            20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "TELNET", 25: "SMTP",
            53: "DNS", 80: "HTTP", 110: "POP3", 111: "RPCBIND", 135: "MSRPC",
            139: "NETBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS",
            995: "POP3S", 1723: "PPTP", 3306: "MYSQL", 3389: "RDP", 5432: "POSTGRESQL",
            5900: "VNC", 8080: "HTTP-ALT", 8443: "HTTPS-ALT", 27017: "MONGODB"
        }
        open_ports = []
        
        def check_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result == 0:
                    return port
            except:
                pass
            return None

        # Use ThreadPoolExecutor for faster scanning
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(check_port, p): p for p in target_ports}
            for future in as_completed(futures):
                p = future.result()
                if p:
                    service = common_ports.get(p, "UNKNOWN")
                    open_ports.append(f"{p} ({service})")
        
        open_ports.sort(key=lambda x: int(x.split()[0]))
            
        if not open_ports:
            return f"No common open ports found on {ip}."
            
        # Security Audit / Remediation Report
        audit_report = self._generate_security_report(ip, open_ports)
        return f"TARGET {ip} OPEN PORTS: {', '.join(open_ports)}\n\n{audit_report}"

    def _is_valid_ip(self, ip):
        """Validate IPv4 address format."""
        import re
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return bool(re.match(pattern, str(ip)))

    def _generate_security_report(self, ip, open_ports):
        """
        Generates a Hardening Report based on open ports.
        Explains theoretical risks and remediation steps (Defensive Audit).
        """
        report = ["=== SECURITY AUDIT & REMEDIATION REPORT ==="]
        report.append(f"Target: {ip}")
        
        for port_desc in open_ports:
            # Extract port number (fix string matching bug)
            port_num = int(port_desc.split()[0])
            
            if port_num == 23:  # TELNET (exact match)
                report.append(f"\n[CRITICAL] Port 23 (Telnet) is OPEN.")
                report.append("  - RISK: Insecure protocol. Passwords sent in cleartext.")
                report.append("  - ATTACK VECTOR: Credential Sniffing / Man-in-the-Middle.")
                report.append("  - REMEDIATION: Disable Telnet immediately. Use SSH (Port 22) instead.")
            
            elif port_num == 21:  # FTP
                report.append(f"\n[HIGH] Port 21 (FTP) is OPEN.")
                report.append("  - RISK: Unencrypted file transfer.")
                report.append("  - REMEDIATION: Switch to SFTP or FTPS.")
                
            elif port_num == 80:  # HTTP
                report.append(f"\n[MEDIUM] Port 80 (HTTP) is OPEN.")
                report.append("  - RISK: Unencrypted web traffic.")
                report.append("  - REMEDIATION: Ensure Administration Panels use HTTPS (Port 443).")
                
            elif port_num == 3389:  # RDP
                report.append(f"\n[MEDIUM] Port 3389 (RDP) is OPEN.")
                report.append("  - RISK: Remote Desktop exposed to LAN.")
                report.append("  - REMEDIATION: Ensure NLA (Network Level Authentication) is enabled and use strong passwords.")
            
            elif port_num == 3306:  # MySQL
                report.append(f"\n[HIGH] Port 3306 (MySQL) is OPEN.")
                report.append("  - RISK: Database exposed to network.")
                report.append("  - REMEDIATION: Bind to localhost only, use strong passwords.")
            
            elif port_num == 5900:  # VNC
                report.append(f"\n[CRITICAL] Port 5900 (VNC) is OPEN.")
                report.append("  - RISK: Remote desktop control, often weak passwords.")
                report.append("  - REMEDIATION: Use SSH tunneling, strong authentication.")
        
        report.append("\n[SUMMARY] To secure this device, close unused ports and update firmware.")
        return "\n".join(report)
