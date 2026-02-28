"""
OSINT Agent — Online Intelligence Gathering.
Coordinates internet-based reconnaissance tools for defensive security auditing.

All API calls are rate-limited and use proper error handling.
Degrades gracefully when offline or when API keys are missing.
"""

import json
import os
import re
import logging
import time
import socket
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("OSINTAgent")


class OSINTAgent:
    """
    Online intelligence gathering agent.
    Coordinates internet-based recon tools for defensive security auditing.
    """
    
    def __init__(self, llm_engine=None):
        self.llm = llm_engine
        self.findings = []
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from .env file."""
        self.api_keys = {}
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        
        try:
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, _, value = line.partition('=')
                            self.api_keys[key.strip()] = value.strip().strip('"').strip("'")
        except Exception as e:
            logger.warning(f"Could not load .env: {e}")
    
    def _is_online(self) -> bool:
        """Check internet connectivity."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    def execute(self, instruction: str) -> str:
        """Parse OSINT instructions and route to appropriate method."""
        instruction_lower = instruction.lower()
        print(f"[OSINT] Executing: {instruction}")
        
        if not self._is_online():
            return "⚠️ No internet connection. OSINT features require network access."
        
        # Route to specific tool
        if "shodan" in instruction_lower:
            target = self._extract_target(instruction)
            return self.shodan_lookup(target) if target else "Please specify target IP."
        
        if "whois" in instruction_lower:
            target = self._extract_domain(instruction)
            return self.whois_lookup(target) if target else "Please specify domain."
        
        if "dns" in instruction_lower or "subdomain" in instruction_lower:
            target = self._extract_domain(instruction)
            return self.dns_recon(target) if target else "Please specify domain."
        
        if "virustotal" in instruction_lower or "vt" in instruction_lower:
            target = self._extract_target(instruction) or self._extract_domain(instruction)
            return self.virustotal_scan(target) if target else "Please specify URL, domain, or hash."
        
        if "exploit" in instruction_lower or "exploitdb" in instruction_lower:
            query = instruction.replace("exploitdb", "").replace("exploit search", "").strip()
            return self.exploitdb_search(query) if query else "Please specify search query."
        
        if "breach" in instruction_lower or "pwned" in instruction_lower:
            email = self._extract_email(instruction)
            return self.breach_check(email) if email else "Please specify email address."
        
        if "recon" in instruction_lower or "full" in instruction_lower:
            target = self._extract_domain(instruction) or self._extract_target(instruction)
            return self.full_recon(target) if target else "Please specify target."
        
        return ("Unknown OSINT command. Try:\n"
                "• 'Shodan [IP]' — check if IP is exposed on the internet\n"
                "• 'WHOIS [domain]' — domain registration info\n"
                "• 'DNS recon [domain]' — DNS records and subdomains\n"
                "• 'VirusTotal [URL/hash]' — malware/phishing check\n"
                "• 'ExploitDB search [query]' — find public exploits\n"
                "• 'Breach check [email]' — check if email was in data breaches\n"
                "• 'Full recon [domain]' — comprehensive OSINT")
    
    # ==================== SHODAN ====================
    
    def shodan_lookup(self, target: str) -> str:
        """Query Shodan for information about an IP address."""
        import requests
        
        api_key = self.api_keys.get('SHODAN_API_KEY', '')
        if not api_key:
            return ("❌ Shodan API key not configured.\n"
                    "Get a free key at https://account.shodan.io/register\n"
                    "Add to .env: SHODAN_API_KEY=your_key_here")
        
        try:
            url = f"https://api.shodan.io/shodan/host/{target}?key={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 404:
                return f"🔍 Shodan — {target}\n   Not found in Shodan database (not exposed to internet)."
            
            if response.status_code != 200:
                return f"❌ Shodan API error: {response.status_code}"
            
            data = response.json()
            
            output = [f"🌐 Shodan Intelligence — {target}"]
            output.append(f"   Organization: {data.get('org', 'Unknown')}")
            output.append(f"   ISP: {data.get('isp', 'Unknown')}")
            output.append(f"   Country: {data.get('country_name', 'Unknown')}")
            output.append(f"   City: {data.get('city', 'Unknown')}")
            output.append(f"   OS: {data.get('os', 'Unknown')}")
            output.append(f"   Last Updated: {data.get('last_update', 'Unknown')}")
            
            # Open ports
            ports = data.get('ports', [])
            if ports:
                output.append(f"\n   Open Ports: {', '.join(str(p) for p in ports)}")
            
            # Vulnerabilities
            vulns = data.get('vulns', [])
            if vulns:
                output.append(f"\n   ⚠️ Known Vulnerabilities ({len(vulns)}):")
                for v in vulns[:10]:
                    output.append(f"   - {v}")
            
            # Services
            for service_data in data.get('data', [])[:5]:
                port = service_data.get('port', '?')
                product = service_data.get('product', 'Unknown')
                version = service_data.get('version', '')
                output.append(f"\n   Port {port}: {product} {version}")
                banner = service_data.get('data', '')[:200]
                if banner:
                    output.append(f"   Banner: {banner}")
            
            self.findings.append({"type": "shodan", "target": target, "data": data})
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Shodan error: {e}"
    
    # ==================== WHOIS ====================
    
    def whois_lookup(self, domain: str) -> str:
        """Perform WHOIS lookup on a domain."""
        try:
            import whois
            
            w = whois.whois(domain)
            
            output = [f"📋 WHOIS — {domain}"]
            output.append(f"   Registrar: {w.registrar or 'Unknown'}")
            output.append(f"   Created: {w.creation_date}")
            output.append(f"   Expires: {w.expiration_date}")
            output.append(f"   Updated: {w.updated_date}")
            
            if w.name_servers:
                ns_list = w.name_servers if isinstance(w.name_servers, list) else [w.name_servers]
                output.append(f"   Name Servers: {', '.join(str(ns) for ns in ns_list[:5])}")
            
            if w.org:
                output.append(f"   Organization: {w.org}")
            
            if w.country:
                output.append(f"   Country: {w.country}")
            
            if w.emails:
                emails = w.emails if isinstance(w.emails, list) else [w.emails]
                output.append(f"   Contact Emails: {', '.join(str(e) for e in emails[:3])}")
            
            self.findings.append({"type": "whois", "target": domain, "data": str(w)})
            return "\n".join(output)
            
        except ImportError:
            return "❌ python-whois not installed. Install: pip install python-whois"
        except Exception as e:
            return f"❌ WHOIS error: {e}"
    
    # ==================== DNS RECON ====================
    
    def dns_recon(self, domain: str) -> str:
        """Perform DNS reconnaissance."""
        try:
            import dns.resolver
            
            output = [f"🔍 DNS Recon — {domain}"]
            
            record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
            
            for rtype in record_types:
                try:
                    answers = dns.resolver.resolve(domain, rtype)
                    records = [str(r) for r in answers]
                    if records:
                        output.append(f"\n   {rtype} Records:")
                        for r in records[:5]:
                            output.append(f"   - {r}")
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                    continue
                except Exception:
                    continue
            
            # Try zone transfer (AXFR)
            output.append(f"\n   Zone Transfer (AXFR):")
            try:
                ns_records = dns.resolver.resolve(domain, 'NS')
                for ns in ns_records:
                    try:
                        import dns.zone
                        import dns.query
                        zone = dns.zone.from_xfr(dns.query.xfr(str(ns), domain, timeout=5))
                        output.append(f"   ⚠️ ZONE TRANSFER SUCCESSFUL from {ns}!")
                        for name, node in zone.nodes.items():
                            output.append(f"   - {name}.{domain}")
                    except Exception:
                        output.append(f"   ✅ {ns} — Zone transfer denied (secure)")
            except Exception:
                output.append(f"   Could not check zone transfer")
            
            # Common subdomain check
            output.append(f"\n   Subdomain Discovery:")
            common_subs = ['www', 'mail', 'ftp', 'admin', 'vpn', 'dev', 'staging', 
                          'api', 'test', 'portal', 'blog', 'shop', 'app', 'cdn',
                          'ns1', 'ns2', 'smtp', 'pop', 'imap', 'webmail']
            
            found_subs = []
            for sub in common_subs:
                try:
                    full = f"{sub}.{domain}"
                    answers = dns.resolver.resolve(full, 'A')
                    ips = [str(r) for r in answers]
                    found_subs.append(f"{full} → {', '.join(ips)}")
                except Exception:
                    continue
            
            if found_subs:
                for s in found_subs:
                    output.append(f"   ✅ {s}")
            else:
                output.append("   No common subdomains found")
            
            self.findings.append({"type": "dns", "target": domain, "subdomains": found_subs})
            return "\n".join(output)
            
        except ImportError:
            return "❌ dnspython not installed. Install: pip install dnspython"
        except Exception as e:
            return f"❌ DNS recon error: {e}"
    
    # ==================== VIRUSTOTAL ====================
    
    def virustotal_scan(self, target: str) -> str:
        """Scan URL, domain, or hash with VirusTotal."""
        import requests
        
        api_key = self.api_keys.get('VIRUSTOTAL_API_KEY', '')
        if not api_key:
            return ("❌ VirusTotal API key not configured.\n"
                    "Get a free key at https://www.virustotal.com/gui/join-us\n"
                    "Add to .env: VIRUSTOTAL_API_KEY=your_key_here")
        
        headers = {"x-apikey": api_key}
        
        try:
            # Determine type: hash, URL, or domain
            if re.match(r'^[a-fA-F0-9]{32,64}$', target):
                # File hash
                url = f"https://www.virustotal.com/api/v3/files/{target}"
            elif '/' in target or target.startswith('http'):
                # URL
                import base64
                url_id = base64.urlsafe_b64encode(target.encode()).decode().strip('=')
                url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
            else:
                # Domain
                url = f"https://www.virustotal.com/api/v3/domains/{target}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return f"❌ VirusTotal error: {response.status_code}"
            
            data = response.json().get('data', {})
            attrs = data.get('attributes', {})
            
            output = [f"🛡️ VirusTotal — {target}"]
            
            stats = attrs.get('last_analysis_stats', {})
            if stats:
                malicious = stats.get('malicious', 0)
                total = sum(stats.values())
                
                if malicious > 0:
                    output.append(f"   ⚠️ {malicious}/{total} engines flagged as MALICIOUS")
                else:
                    output.append(f"   ✅ {total} engines scanned — CLEAN")
                
                output.append(f"   Harmless: {stats.get('harmless', 0)}")
                output.append(f"   Suspicious: {stats.get('suspicious', 0)}")
                output.append(f"   Undetected: {stats.get('undetected', 0)}")
            
            # Reputation
            reputation = attrs.get('reputation', None)
            if reputation is not None:
                output.append(f"   Reputation Score: {reputation}")
            
            # Categories
            categories = attrs.get('categories', {})
            if categories:
                output.append(f"   Categories: {', '.join(categories.values())}")
            
            self.findings.append({"type": "virustotal", "target": target, "stats": stats})
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ VirusTotal error: {e}"
    
    # ==================== EXPLOITDB ====================
    
    def exploitdb_search(self, query: str) -> str:
        """Search ExploitDB for public exploits."""
        import requests
        
        try:
            # Use ExploitDB API (via exploit-database.com search page)
            url = f"https://www.exploit-db.com/search"
            params = {"q": query}
            headers = {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                # Fallback: use searchsploit locally
                return self._searchsploit(query)
            
            data = response.json()
            exploits = data.get('data', [])
            
            output = [f"💀 ExploitDB — \"{query}\""]
            output.append(f"   Found: {len(exploits)} exploits\n")
            
            for exp in exploits[:10]:
                output.append(f"   [{exp.get('id', '?')}] {exp.get('description', {}).get('description', 'N/A')}")
                output.append(f"   Platform: {exp.get('platform', {}).get('platform', 'N/A')} | Type: {exp.get('type', {}).get('type', 'N/A')}")
                output.append("")
            
            return "\n".join(output)
            
        except Exception:
            return self._searchsploit(query)
    
    def _searchsploit(self, query: str) -> str:
        """Fallback to local searchsploit if available."""
        import subprocess
        import shutil
        
        if not shutil.which("searchsploit"):
            return f"❌ searchsploit not installed and ExploitDB API unavailable.\nInstall: apt install exploitdb"
        
        try:
            result = subprocess.run(
                ["searchsploit", "--json", query],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                exploits = data.get('RESULTS_EXPLOIT', [])
                
                output = [f"💀 SearchSploit — \"{query}\""]
                output.append(f"   Found: {len(exploits)} exploits\n")
                
                for exp in exploits[:10]:
                    output.append(f"   [{exp.get('EDB-ID', '?')}] {exp.get('Title', 'N/A')}")
                    output.append(f"   Path: {exp.get('Path', 'N/A')}")
                    output.append("")
                
                return "\n".join(output)
            
            return f"searchsploit returned no results for '{query}'"
            
        except Exception as e:
            return f"❌ searchsploit error: {e}"
    
    # ==================== BREACH CHECK ====================
    
    def breach_check(self, email: str) -> str:
        """Check if email was in known data breaches."""
        import requests
        
        try:
            # Use HaveIBeenPwned-style check via alternative free API
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            headers = {"hibp-api-key": self.api_keys.get('HIBP_API_KEY', ''),
                      "user-agent": "FRIDAY-Security-Auditor"}
            
            if not headers['hibp-api-key']:
                return ("❌ HaveIBeenPwned API key not configured.\n"
                        "Get a key at https://haveibeenpwned.com/API/Key\n"  
                        "Add to .env: HIBP_API_KEY=your_key_here")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 404:
                return f"✅ {email} — Not found in any known data breaches!"
            
            if response.status_code != 200:
                return f"❌ HIBP API error: {response.status_code}"
            
            breaches = response.json()
            
            output = [f"⚠️ Breach Report — {email}"]
            output.append(f"   Found in {len(breaches)} breach(es)!\n")
            
            for b in breaches[:5]:
                output.append(f"   🔓 {b.get('Name', 'Unknown')}")
                output.append(f"      Date: {b.get('BreachDate', 'Unknown')}")
                output.append(f"      Data: {', '.join(b.get('DataClasses', []))}")
                output.append("")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Breach check error: {e}"
    
    # ==================== FULL RECON ====================
    
    def full_recon(self, target: str) -> str:
        """Run comprehensive OSINT on a target."""
        output = [f"🎯 Full OSINT Reconnaissance — {target}\n"]
        output.append("=" * 50)
        
        # WHOIS
        output.append("\n" + self.whois_lookup(target))
        
        # DNS
        output.append("\n" + self.dns_recon(target))
        
        # VirusTotal
        output.append("\n" + self.virustotal_scan(target))
        
        # Shodan (if IP)
        if re.match(r'\d+\.\d+\.\d+\.\d+', target):
            output.append("\n" + self.shodan_lookup(target))
        else:
            # Resolve domain to IP
            try:
                ip = socket.gethostbyname(target)
                output.append(f"\n   Resolved {target} → {ip}")
                output.append("\n" + self.shodan_lookup(ip))
            except Exception:
                output.append("\n   Could not resolve domain for Shodan lookup")
        
        # ExploitDB
        output.append("\n" + self.exploitdb_search(target))
        
        output.append("\n" + "=" * 50)
        output.append("OSINT Reconnaissance Complete.")
        
        return "\n".join(output)
    
    # ==================== HELPERS ====================
    
    def _extract_target(self, text: str) -> Optional[str]:
        """Extract IP or URL from text."""
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
        if ips:
            return ips[0]
        urls = re.findall(r'https?://\S+', text)
        if urls:
            return urls[0]
        return None
    
    def _extract_domain(self, text: str) -> Optional[str]:
        """Extract domain name from text."""
        domains = re.findall(r'\b([a-zA-Z0-9][\w\-]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)\b', text)
        # Filter out common words that match domain pattern
        filtered = [d for d in domains if d.lower() not in 
                   ['shodan.io', 'osint.agent', 'bug.hunter', 'dns.recon']]
        return filtered[0] if filtered else None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text."""
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
        return emails[0] if emails else None
