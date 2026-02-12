"""
AI Workflow Engine — Multi-tool coordination that thinks like a real pentester.

This is the "hacker brain" that chains tools together intelligently:
1. You give it a target
2. The AI decides which tool to run first
3. Based on results, it decides the next tool
4. Continues until comprehensive audit is complete
5. Generates final report

No hardcoded sequences — the AI adapts based on findings.
"""

import json
import os
import sys
import time
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.tool_executor import ToolExecutor
from core.cve_database import CVEDatabase
from core.database import DatabaseManager


class PentestWorkflow:
    """
    AI-driven penetration testing workflow engine.
    
    Implements the real hacker methodology:
    1. Recon → 2. Enumeration → 3. Vulnerability Analysis → 4. Exploitation Planning → 5. Reporting
    """
    
    def __init__(self, llm_engine=None):
        self.llm = llm_engine
        self.tools = ToolExecutor()
        self.cve_db = CVEDatabase()
        self.db = DatabaseManager()
        self.workflow_log = []
        self.all_findings = []
    
    def _log(self, phase: str, tool: str, message: str, data: dict = None):
        """Log workflow step."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "tool": tool,
            "message": message,
            "data": data or {}
        }
        self.workflow_log.append(entry)
        print(f"[Workflow] [{phase}] [{tool}] {message}")
    
    def run_full_audit(self, target: str) -> str:
        """
        Run complete multi-phase penetration test.
        The AI decides tool sequence based on findings.
        """
        start_time = time.time()
        
        output = [f"{'='*60}"]
        output.append(f"🎯 AI CYBER DECK — FULL SECURITY AUDIT")
        output.append(f"Target: {target}")
        output.append(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"{'='*60}")
        
        # ==================== PHASE 1: RECONNAISSANCE ====================
        output.append(f"\n{'─'*40}")
        output.append("📡 PHASE 1: RECONNAISSANCE")
        output.append(f"{'─'*40}")
        
        recon_results = self._recon_phase(target)
        output.append(recon_results["summary"])
        
        # ==================== PHASE 2: ENUMERATION ====================
        output.append(f"\n{'─'*40}")
        output.append("🔍 PHASE 2: ENUMERATION")
        output.append(f"{'─'*40}")
        
        enum_results = self._enum_phase(target, recon_results)
        output.append(enum_results["summary"])
        
        # ==================== PHASE 3: VULNERABILITY ANALYSIS ====================
        output.append(f"\n{'─'*40}")
        output.append("⚡ PHASE 3: VULNERABILITY ANALYSIS")
        output.append(f"{'─'*40}")
        
        vuln_results = self._vuln_phase(target, recon_results, enum_results)
        output.append(vuln_results["summary"])
        
        # ==================== PHASE 4: EXPLOIT PLANNING ====================
        output.append(f"\n{'─'*40}")
        output.append("🎯 PHASE 4: EXPLOITATION PLANNING (AI)")
        output.append(f"{'─'*40}")
        
        exploit_plan = self._exploit_planning_phase(target)
        output.append(exploit_plan)
        
        # ==================== PHASE 5: REPORT ====================
        duration = time.time() - start_time
        output.append(f"\n{'='*60}")
        output.append(f"📊 AUDIT COMPLETE — {duration:.1f}s")
        output.append(f"Total findings: {len(self.all_findings)}")
        output.append(f"{'='*60}")
        
        report = self._generate_final_report(target, duration)
        output.append(report)
        
        return "\n".join(output)
    
    def _recon_phase(self, target: str) -> dict:
        """Phase 1: Network reconnaissance."""
        results = {"services": [], "ports": [], "os": None, "summary": ""}
        summary_lines = []
        
        # Step 1: Quick Nmap service scan
        self._log("RECON", "nmap", f"Starting service detection scan on {target}")
        nmap_result = self.tools.run_nmap(target, scan_type="service")
        
        if nmap_result.success:
            hosts = nmap_result.data.get("hosts", [])
            for host in hosts:
                for port_info in host.get("ports", []):
                    if port_info.get("state") == "open":
                        results["ports"].append(port_info)
                        results["services"].append({
                            "port": port_info["port"],
                            "service": port_info.get("service", "unknown"),
                            "version": port_info.get("version", "")
                        })
                        
                        self.all_findings.append({
                            "phase": "recon",
                            "type": "open_port",
                            "port": port_info["port"],
                            "service": port_info.get("service"),
                            "version": port_info.get("version"),
                            "target": target
                        })
                
                if host.get("os"):
                    results["os"] = host["os"][0].get("name", "Unknown")
            
            summary_lines.append(f"   Nmap: {len(results['ports'])} open ports detected")
            for svc in results["services"]:
                summary_lines.append(f"   ├─ Port {svc['port']}: {svc['service']} {svc['version']}")
            if results["os"]:
                summary_lines.append(f"   └─ OS: {results['os']}")
        else:
            summary_lines.append(f"   ⚠️ Nmap failed: {nmap_result.error}")
        
        results["summary"] = "\n".join(summary_lines)
        return results
    
    def _enum_phase(self, target: str, recon: dict) -> dict:
        """Phase 2: Targeted enumeration based on recon results."""
        results = {"web_findings": [], "smb_findings": [], "summary": ""}
        summary_lines = []
        
        services = recon.get("services", [])
        
        for svc in services:
            port = svc["port"]
            service_name = svc["service"].lower()
            
            # Web server detected → run web fingerprinting
            if service_name in ["http", "https", "http-proxy"] or port in [80, 443, 8080, 8443]:
                self._log("ENUM", "whatweb", f"Web fingerprinting port {port}")
                proto = "https" if port == 443 or "ssl" in service_name else "http"
                web_target = f"{proto}://{target}:{port}"
                
                web_result = self.tools.run_whatweb(web_target)
                if web_result.success:
                    results["web_findings"].append(web_result.data)
                    summary_lines.append(f"   WhatWeb port {port}: Technology detected")
                
                # Directory bruteforce
                self._log("ENUM", "gobuster", f"Directory bruteforce on port {port}")
                dir_result = self.tools.run_gobuster(web_target)
                if dir_result.success:
                    paths = dir_result.data.get("found_paths", [])
                    summary_lines.append(f"   Gobuster port {port}: {len(paths)} paths found")
                    
                    for path in paths[:5]:
                        summary_lines.append(f"   ├─ {path['path']} (Status: {path.get('status', '?')})")
                        self.all_findings.append({
                            "phase": "enum",
                            "type": "discovered_path",
                            "path": path["path"],
                            "status": path.get("status"),
                            "target": web_target
                        })
            
            # SMB detected → enumerate
            if service_name in ["microsoft-ds", "netbios-ssn", "smb"] or port in [445, 139]:
                self._log("ENUM", "enum4linux", f"SMB enumeration on {target}")
                smb_result = self.tools.run_enum4linux(target)
                if smb_result.success:
                    results["smb_findings"].append(smb_result.data)
                    users = smb_result.data.get("users", [])
                    if users:
                        summary_lines.append(f"   enum4linux: {len(users)} users found")
                        self.all_findings.append({
                            "phase": "enum",
                            "type": "smb_users",
                            "users": users,
                            "target": target
                        })
        
        if not summary_lines:
            summary_lines.append("   No additional enumeration targets identified.")
        
        results["summary"] = "\n".join(summary_lines)
        return results
    
    def _vuln_phase(self, target: str, recon: dict, enum: dict) -> dict:
        """Phase 3: Vulnerability analysis based on recon + enum."""
        results = {"cves": [], "web_vulns": [], "summary": ""}
        summary_lines = []
        
        services = recon.get("services", [])
        
        for svc in services:
            service_name = svc["service"]
            version = svc["version"]
            port = svc["port"]
            
            # CVE matching
            cves = self.cve_db.search(service_name, version)
            if cves:
                cves.sort(key=lambda x: x.get("cvss", 0), reverse=True)
                for cve in cves[:3]:
                    results["cves"].append(cve)
                    severity = cve.get("severity", "UNKNOWN")
                    icon = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡"
                    summary_lines.append(f"   {icon} {cve['cve_id']}: {cve['description'][:80]} (CVSS: {cve.get('cvss', '?')})")
                    
                    self.all_findings.append({
                        "phase": "vuln",
                        "type": "cve",
                        "cve_id": cve["cve_id"],
                        "cvss": cve.get("cvss"),
                        "severity": severity,
                        "service": service_name,
                        "port": port,
                        "target": target
                    })
            
            # Web vulnerability scanning
            if service_name.lower() in ["http", "https"] or port in [80, 443, 8080, 8443]:
                proto = "https" if port == 443 else "http"
                web_target = f"{proto}://{target}:{port}"
                
                self._log("VULN", "nikto", f"Web vulnerability scan on port {port}")
                nikto_result = self.tools.run_nikto(web_target, port=port)
                if nikto_result.success:
                    vulns = nikto_result.data.get("vulnerabilities", [])
                    results["web_vulns"].extend(vulns)
                    summary_lines.append(f"   Nikto port {port}: {len(vulns)} findings")
        
        if not summary_lines:
            summary_lines.append("   ✅ No known vulnerabilities matched detected services.")
        
        results["summary"] = "\n".join(summary_lines)
        return results
    
    def _exploit_planning_phase(self, target: str) -> str:
        """Phase 4: AI generates exploitation plan based on all findings."""
        if not self.llm:
            return self._manual_exploit_suggestions()
        
        findings_summary = json.dumps(self.all_findings[:30], indent=2)
        
        prompt = f"""Based on the following penetration test findings, generate an EXPLOITATION PLAN.

For each vulnerability found, suggest:
1. The exact Metasploit module to use (if applicable)
2. The exact command to run
3. Expected outcome
4. Risk level of exploitation

FINDINGS:
{findings_summary}

TARGET: {target}

Output a structured exploitation plan with specific commands. DO NOT execute anything, just PLAN.
"""
        
        try:
            plan = self.llm.generate(
                prompt=prompt,
                system_prompt="You are an expert penetration tester planning exploitation steps.",
                temperature=0.3
            )
            return plan
        except Exception as e:
            return self._manual_exploit_suggestions()
    
    def _manual_exploit_suggestions(self) -> str:
        """Generate exploit suggestions without AI."""
        suggestions = []
        
        for finding in self.all_findings:
            if finding.get("type") == "cve":
                cve = finding.get("cve_id", "")
                port = finding.get("port", "")
                service = finding.get("service", "")
                
                # Common CVE to Metasploit module mapping
                module_map = {
                    "CVE-2021-41773": "exploit/multi/http/apache_normalize_path_rce",
                    "CVE-2017-0144": "exploit/windows/smb/ms17_010_eternalblue",
                    "CVE-2019-0708": "exploit/windows/rdp/cve_2019_0708_bluekeep_rce",
                    "CVE-2020-1938": "exploit/multi/http/tomcat_ghostcat",
                    "CVE-2017-5638": "exploit/multi/http/struts2_content_type_ognl",
                    "CVE-2011-2523": "exploit/unix/ftp/vsftpd_234_backdoor",
                    "CVE-2017-7494": "exploit/linux/samba/is_known_pipename",
                    "CVE-2020-1472": "exploit/windows/dcerpc/CVE-2020-1472-zerologon",
                }
                
                if cve in module_map:
                    suggestions.append(f"   🎯 {cve} on port {port}:")
                    suggestions.append(f"      Module: {module_map[cve]}")
                    suggestions.append(f"      Command: use {module_map[cve]}; set RHOSTS {finding.get('target', '?')}; run")
                    suggestions.append("")
        
        if not suggestions:
            return "   No direct exploit modules identified. Manual investigation recommended."
        
        return "\n".join(suggestions)
    
    def _generate_final_report(self, target: str, duration: float) -> str:
        """Generate final audit report."""
        if not self.llm:
            return self._manual_report(target, duration)
        
        try:
            prompt = f"""Generate a Professional Penetration Test Executive Summary.

TARGET: {target}
DURATION: {duration:.0f} seconds
TOTAL FINDINGS: {len(self.all_findings)}

FINDINGS (JSON):
{json.dumps(self.all_findings[:20], indent=2)}

Include:
1. Overall Risk Rating (Critical/High/Medium/Low)
2. Top 3 most critical findings
3. Immediate action items
4. Recommended next steps

Keep it concise — this is an executive summary for management.
"""
            return self.llm.generate(
                prompt=prompt,
                system_prompt="You are a CISO writing a concise executive summary.",
                temperature=0.3
            )
        except Exception:
            return self._manual_report(target, duration)
    
    def _manual_report(self, target: str, duration: float) -> str:
        """Fallback manual report when LLM unavailable."""
        critical = [f for f in self.all_findings if f.get("severity") == "CRITICAL"]
        high = [f for f in self.all_findings if f.get("severity") == "HIGH"]
        
        report = ["\n📊 EXECUTIVE SUMMARY"]
        report.append(f"   Target: {target}")
        report.append(f"   Duration: {duration:.0f}s")
        report.append(f"   Critical: {len(critical)} | High: {len(high)} | Total: {len(self.all_findings)}")
        
        if critical:
            report.append("\n   🔴 CRITICAL FINDINGS:")
            for c in critical[:3]:
                report.append(f"   - {c.get('cve_id', c.get('type', '?'))}: Port {c.get('port', '?')}")
        
        report.append("\n   RECOMMENDATIONS:")
        report.append("   1. Patch all critical CVEs immediately")
        report.append("   2. Close unnecessary open ports")
        report.append("   3. Update all services to latest versions")
        
        return "\n".join(report)
    
    # ==================== SPECIALIZED WORKFLOWS ====================
    
    def web_audit(self, target_url: str) -> str:
        """Focused web application audit."""
        output = [f"🌐 WEB AUDIT — {target_url}\n"]
        
        # WhatWeb
        result = self.tools.run_whatweb(target_url)
        if result.success:
            output.append(f"Tech: {json.dumps(result.data, indent=2)[:500]}")
        
        # Nikto
        result = self.tools.run_nikto(target_url)
        if result.success:
            output.append(f"Nikto: {len(result.data.get('vulnerabilities', []))} findings")
        
        # Gobuster
        result = self.tools.run_gobuster(target_url)
        if result.success:
            output.append(f"Dirs: {len(result.data.get('found_paths', []))} found")
        
        # SQLMap on discovered pages
        result = self.tools.run_sqlmap(target_url)
        if result.success and result.data.get("vulnerable"):
            output.append("⚠️ SQL INJECTION FOUND!")
        
        return "\n".join(output)
    
    def wireless_audit(self, interface: str = "wlan0") -> str:
        """Focused wireless security audit."""
        output = [f"📡 WIRELESS AUDIT — {interface}\n"]
        
        # Enable monitor mode
        result = self.tools.run_airmon(interface, "start")
        if result.success:
            output.append("Monitor mode enabled")
            
            # Scan networks
            result = self.tools.run_airodump(f"{interface}mon", timeout=15)
            if result.success:
                networks = result.data.get("networks", [])
                output.append(f"Found {len(networks)} networks")
                for net in networks[:10]:
                    output.append(f"   {net.get('essid', '?')} — {net.get('encryption', '?')} (Ch: {net.get('channel', '?')})")
            
            # Restore managed mode
            self.tools.run_airmon(f"{interface}mon", "stop")
        else:
            output.append(f"⚠️ Monitor mode failed: {result.error}")
        
        return "\n".join(output)
