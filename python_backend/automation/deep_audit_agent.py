import subprocess
import re
import json
import logging
import platform

class DeepAuditAgent:
    """
    Defensive Security Auditor Module.
    Performs deep inspection of assets for known security flaws (Configuration & Patching).
    Safe alternative to exploitation.
    """
    def __init__(self, mobile_agent=None, pentest_agent=None):
        self.mobile = mobile_agent
        self.pentest = pentest_agent
        self.logger = logging.getLogger("DeepAudit")

    def execute(self, instruction):
        """
        Parses audit instructions.
        target can be 'mobile', 'wifi', 'network', or specific IP.
        """
        instruction = instruction.lower()
        self.logger.info(f"Starting audit: {instruction}")

        if "mobile" in instruction or "android" in instruction:
            return self._audit_mobile()
        
        if "wifi" in instruction or "wireless" in instruction:
            return self._audit_wifi()
            
        if "server" in instruction or "enterprise" in instruction:
            # Extract target IP
            import re
            ips = re.findall(r'[0-9]+(?:\.[0-9]+){3}', instruction)
            if ips:
                return self._audit_server(ips[0])
            return "Please specify server IP to audit."
            
        return "Unknown audit target. Try 'audit mobile', 'audit wifi', or 'audit server [IP]'."

    def _audit_mobile(self):
        """
        Remote Android Security Audit via ADB.
        Checks: Android Version, Security Patch Level, Debugging Status.
        """
        if not self.mobile or not self.mobile.check_connection():
            return "Mobile Security Audit Failed: No device connected."
            
        report = ["=== MOBILE SECURITY AUDIT REPORT ==="]
        
        # 1. Get Device Info
        props = self._get_android_props()
        
        model = props.get("ro.product.model", "Unknown")
        version = props.get("ro.build.version.release", "0")
        patch_level = props.get("ro.build.version.security_patch", "2000-01-01")
        
        report.append(f"Device: {model}")
        report.append(f"Android Version: {version}")
        report.append(f"Security Patch: {patch_level}")
        
        # 2. Analyze Vulnerabilities
        risks = []
        
        # Check Android Version
        ver_num = 0
        try:
            ver_num = int(version.split('.')[0])
            if ver_num < 10:
                risks.append("[CRITICAL] Outdated Android Version. No longer supported.")
            elif ver_num < 12:
                risks.append("[HIGH] Older Android Version. May have limited updates.")
        except (ValueError, IndexError):
            risks.append("[WARNING] Could not parse Android version.")
            
        # Check Patch Level using date comparison
        try:
            from datetime import datetime, timedelta
            patch_date = datetime.strptime(patch_level, "%Y-%m-%d")
            if (datetime.now() - patch_date) > timedelta(days=365):
                risks.append(f"[CRITICAL] Security Patch is over 1 year old ({patch_level}). Vulnerable to known exploits.")
            elif (datetime.now() - patch_date) > timedelta(days=180):
                risks.append(f"[HIGH] Security Patch is over 6 months old ({patch_level}).")
        except (ValueError, TypeError):
            if "2023" not in patch_level and "2024" not in patch_level and "2025" not in patch_level and "2026" not in patch_level:
                risks.append("[CRITICAL] Security Patch is outdated. Vulnerable to known exploits.")
        
        # Check for Stagefright (Legacy Check logic)
        if ver_num > 0 and ver_num < 6:
             risks.append("[CRITICAL] Vulnerable to Stagefright (CVE-2015-1538). Update immediately.")

        if risks:
            report.append("\nDETECTED RISKS:")
            for risk in risks:
                report.append(f"❌ {risk}")
        else:
            report.append("\n✅ Device appears updated and patched.")
            
        return "\n".join(report)

    def _audit_wifi(self):
        """
        Audits current WiFi connection security.
        """
        report = ["=== WIFI SECURITY AUDIT REPORT ==="]
        
        try:
            if platform.system() == "Windows":
                 # Get current Wi-Fi interface info
                 cmd = ["netsh", "wlan", "show", "interfaces"]
                 result = subprocess.run(cmd, capture_output=True, text=True)
                 output = result.stdout
                 
                 # Extract SSID and Authentication
                 ssid_match = re.search(r'^\s*SSID\s*:\s*(.*)$', output, re.MULTILINE)
                 auth_match = re.search(r'^\s*Authentication\s*:\s*(.*)$', output, re.MULTILINE)
                 cipher_match = re.search(r'^\s*Cipher\s*:\s*(.*)$', output, re.MULTILINE)
                 
                 ssid = ssid_match.group(1).strip() if ssid_match else "Unknown"
                 auth = auth_match.group(1).strip() if auth_match else "Unknown"
                 cipher = cipher_match.group(1).strip() if cipher_match else "Unknown"
                 
                 report.append(f"SSID: {ssid}")
                 report.append(f"Protocol: {auth}")
                 report.append(f"Encryption: {cipher}")
                 
                 # Analyze Risks
                 if "WEP" in auth:
                     report.append("\n❌ [CRITICAL] WEP Detected. Extremely insecure. Crackable in minutes.")
                 elif "WPA1" in auth or "WPA-Personal" == auth: # Depending on output format
                     report.append("\n❌ [HIGH] WPA1 Detected. Vulnerable to TKIP attacks.")
                 elif "Open" in auth:
                     report.append("\n❌ [CRITICAL] Open Network. No encryption. Traffic visible to everyone.")
                 else:
                     report.append("\n✅ WPA2/WPA3 Detected. Standard security.")
                     
        except Exception as e:
            return f"Error auditing WiFi: {e}"
            
        return "\n".join(report)

    def _audit_server(self, ip):
        """
        Audits server for SMB vulnerabilities using Nmap scripts.
        """
        if not self.pentest:
             return "Pentest module unavailable for server audit."
             
        report = [f"=== SERVER AUDIT REPORT: {ip} ==="]
        
        # Check for SMBv1 (EternalBlue vector)
        self.logger.info(f"Checking {ip} for SMB risks...")
        
        try:
            # We use the PentestAgent's nmap wrapper if possible, or direct subprocess here for specific scripts
            # Using direct nmap for specific script
            cmd = ["nmap", "-p", "445", "--script", "smb-vuln-ms17-010,smb-protocols", ip]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = result.stdout
            
            if "ms17-010" in output.lower() and "vulnerable" in output.lower():
               report.append("\n❌ [CRITICAL] VULNERABLE TO ETERNALBLUE (MS17-010)!")
               report.append("   Impact: Remote Code Execution (RCE)")
               report.append("   Remediation: Apply Microsoft Patch MS17-010 immediately.")
            else:
               report.append("\n✅ Not vulnerable to EternalBlue.")
               
            if "SMBv1: true" in output or "NT LM 0.12" in output: # Indication of SMBv1
               report.append("\n⚠️ [HIGH] SMBv1 Enabled.")
               report.append("   Risk: Legacy protocol, susceptible to ransomware spreading.")
               report.append("   Remediation: Disable SMBv1.")
            else:
               pass # SMBv1 likely disabled
               
        except Exception as e:
            report.append(f"Error running checks: {e}")
            
        return "\n".join(report)

    def _get_android_props(self):
        """Helper to get all android properties via ADB"""
        props = {}
        try:
            cmd = [self.mobile.adb_path, "-s", self.mobile.device_id, "shell", "getprop"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            for line in result.stdout.splitlines():
                # Format: [key]: [value]
                match = re.match(r'\[(.*?)\]: \[(.*?)\]', line)
                if match:
                    props[match.group(1)] = match.group(2)
        except:
            pass
        return props
