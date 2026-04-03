import json
import os

def create_1000_agents():
    registry = {}
    
    # Base tools and variations
    tools = {
        "nmap": ["stealth", "aggressive", "syn", "udp", "vuln", "fast", "allports", "ping", "traceroute", "sctp", "ipv6", "os_detect"],
        "hydra": ["ssh", "ftp", "telnet", "rdp", "mysql", "postgres", "smb", "http_get", "http_post", "vnc", "pop3", "imap"],
        "sqlmap": ["blind", "time_based", "error_based", "union", "inline", "fingerprint", "os_pwn", "file_read", "file_write"],
        "metasploit": ["reverse_tcp", "bind_tcp", "stager", "meterpreter", "windows_smb", "linux_ssh", "android_tcp", "web_delivery"],
        "gobuster": ["dir", "dns", "vhost", "s3", "fuzz", "tftp", "gcs"],
        "ffuf": ["subdomains", "directories", "parameters", "headers", "post_data"],
        "nikto": ["standard", "ssl", "tuning_1", "tuning_2", "tuning_4"],
        "shodan": ["host", "search", "stats", "facets", "exploits", "honeyscore"],
        "flipper": ["subghz_tx", "subghz_rx", "rfid_clone", "rfid_emulate", "nfc_read", "nfc_emulate", "ir_tx", "ir_rx", "ibutton", "badusb"],
        "wifi": ["airmon", "airodump", "aireplay", "aircrack", "reaver", "wifite", "bully", "hostapd"],
        "bluetooth": ["hcitool", "l2ping", "sdptool", "hcidump", "btscanner"],
        "mitm": ["arpspoof", "dnsspoof", "dsniff", "ettercap", "bettercap", "mitmproxy"],
        "osint": ["whois", "dig", "theharvester", "recon-ng", "spiderfoot", "maltego_cli", "sherlock"],
        "mobile": ["adb_shell", "adb_pull", "adb_install", "apktool_d", "apktool_b", "signapk", "frida_trace", "objection"],
        "cloud": ["aws_s3_ls", "aws_iam_list", "gcp_enum", "azure_ad_recon", "pacu"],
        "iot": ["mqtt_sub", "mqtt_pub", "coap_get", "modbus_read", "s7_info"]
    }
    
    expert_id = 1
    
    # 1. Generate core tactical variants (Tool x Tactic x Protocol x Environment)
    for tool, variants in tools.items():
        for variant in variants:
            for env in ["internal", "external", "dmz", "cloud"]:
                for intensity in ["low", "medium", "high", "insane"]:
                    name = f"{tool}_{variant}_{env}_{intensity}"
                    
                    registry[name] = {
                        "id": f"EXP-{expert_id:04d}",
                        "name": f"{tool.capitalize()} {variant.capitalize()} Specialist ({env.upper()}, Intensity {intensity.upper()})",
                        "tool": tool,
                        "variant": variant,
                        "environment": env,
                        "intensity": intensity,
                        "description": f"Specializes in {intensity} intensity {tool} operations focusing on {variant} within {env} targets.",
                        "system_prompt": f"YOU ARE EXP-{expert_id:04d}, THE {tool.upper()} {variant.upper()} EXPERT. Your focus is {intensity} intensity operations on {env} targets. Formulate precise {tool} commands.",
                        "capabilities": [tool, variant, env]
                    }
                    expert_id += 1
                    
                    if expert_id > 1000:
                        break
                if expert_id > 1000: break
            if expert_id > 1000: break
        if expert_id > 1000: break

    # 2. If we haven't reached 1000, fill out with specific CVE/Exploit specialists
    if expert_id <= 1000:
        cve_years = range(2010, 2025)
        categories = ["rce", "lpe", "sqli", "xss", "ssrf", "xxe", "deserialization", "auth_bypass"]
        systems = ["windows", "linux", "macos", "android", "ios", "cisco", "apache", "nginx", "wordpress", "drupal"]
        
        for year in cve_years:
            for cat in categories:
                for sys in systems:
                    name = f"cve_hunter_{sys}_{cat}_{year}"
                    registry[name] = {
                        "id": f"EXP-{expert_id:04d}",
                        "name": f"CVE {year} {sys.capitalize()} {cat.upper()} Specialist",
                        "tool": "metasploit",
                        "variant": "cve_hunter",
                        "environment": sys,
                        "intensity": "high",
                        "description": f"Specializes in weaponizing and hunting {sys} {cat} vulnerabilities from {year}.",
                        "system_prompt": f"YOU ARE EXP-{expert_id:04d}, THE {sys.upper()} {cat.upper()} {year} SPECIALIST. Deploy exploits mapping to these CVEs.",
                        "capabilities": [sys, cat, str(year)]
                    }
                    expert_id += 1
                    if expert_id > 1000:
                        break
                if expert_id > 1000: break
            if expert_id > 1000: break

    # Ensure output directory exists
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
    os.makedirs(config_dir, exist_ok=True)
    
    # Save the huge registry
    registry_path = os.path.join(config_dir, "expert_registry.json")
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=4)
        
    print(f"Generated {len(registry)} agent profiles in {registry_path}.")

if __name__ == "__main__":
    create_1000_agents()
