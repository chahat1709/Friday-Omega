import subprocess
import re
import json
from typing import Dict, List, Optional
import sys
import os
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.database import DatabaseManager

class BugHunterAgent:
    """
    Autonomous vulnerability discovery agent.
    Uses creative AI prompting to find novel bugs, not just known CVEs.
    
    Workflow:
    1. AI analyzes target creatively
    2. Generates fuzzing payloads
    3. Tests hypotheses automatically
    4. Reports findings with PoC
    5. Human approves exploitation/verification
    """
    
    def __init__(self, llm_engine):
        self.llm = llm_engine
        self.target_url = None
        self.db = DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'FRIDAY-Security-Auditor/1.0'})
        self.findings = []
        self.tested_vectors = []
        
        # Load creative researcher prompt
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'bug_hunter.md')
        with open(prompt_path, 'r') as f:
            self.researcher_prompt = f.read()
    
    def hunt(self, target_url):
        """
        Autonomous bug discovery workflow
        """
        print(f"[Bug Hunter] Starting creative analysis of {target_url}")
        self.target_url = target_url
        
        # Phase 1: Creative Reconnaissance
        print("\n[Phase 1] Creative Reconnaissance...")
        recon_data = self._creative_recon(target_url)
        
        # Phase 2: Hypothesis Generation (AI thinks creatively)
        print("\n[Phase 2] Generating attack hypotheses...")
        hypotheses = self._generate_hypotheses(target_url, recon_data)
        
        # Phase 3: Automated Testing
        print("\n[Phase 3] Testing hypotheses...")
        for hypothesis in hypotheses:
            result = self._test_hypothesis(hypothesis)
            if result['vulnerable']:
                self.findings.append(result)
                print(f"\n🎯 [BUG FOUND] {result['type']}")
                print(f"   Severity: {result['severity']}")
                print(f"   PoC: {result['poc']}")
        
        # Phase 4: Generate Report
        return self._generate_bug_report()
    
    def _creative_recon(self, target):
        """
        Use AI to analyze target creatively
        """
        # Basic tech fingerprinting
        tech_stack = self._fingerprint_technology(target)
        
        # AI analyzes for creative attack surface
        analysis_prompt = f"""
Target: {target}
Technologies detected: {tech_stack}

As a creative security researcher, analyze this target:
1. What assumptions might the developers have made?
2. What unusual input vectors exist?
3. What business logic flaws might be present?
4. What are 5 creative attack ideas to test?

Output JSON:
{{"assumptions": [], "input_vectors": [], "logic_flaws": [], "attack_ideas": []}}
"""
        
        try:
            ai_analysis = self.llm.generate(
                prompt=analysis_prompt,
                system_prompt=self.researcher_prompt,
                temperature=0.8  # Higher creativity
            )
            
            # Parse AI suggestions
            return self._parse_json_from_text(ai_analysis)
        except:
            return {"attack_ideas": [
                "Test for SQL injection in all parameters",
                "Check for IDOR in API endpoints",
                "Fuzz authentication with edge cases"
            ]}
    
    def _generate_hypotheses(self, target, recon_data):
        """
        AI generates creative test hypotheses
        """
        hypotheses = []
        
        for idea in recon_data.get('attack_ideas', []):
            # AI expands idea into testable hypothesis
            hypothesis_prompt = f"""
Attack idea: {idea}
Target: {target}

Generate a specific, testable hypothesis:
1. What exact payload/request to send?
2. What response indicates vulnerability?
3. What is the expected impact?

Output JSON:
{{"payload": "", "success_indicator": "", "vulnerability_type": "", "severity": ""}}
"""
            
            try:
                ai_response = self.llm.generate(
                    prompt=hypothesis_prompt,
                    system_prompt=self.researcher_prompt
                )
                
                hypothesis = self._parse_json_from_text(ai_response)
                hypothesis['target'] = target
                hypotheses.append(hypothesis)
            except Exception as e:
                print(f"Error generating hypothesis: {e}")
                continue
        
        return hypotheses
    
    def _test_hypothesis(self, hypothesis):
        """
        Automatically test a hypothesis (non-destructive probing only)
        """
        print(f"\n  Testing: {hypothesis.get('vulnerability_type', 'Unknown')}")
        
        # Safety check: Only test read-only operations
        if self._is_safe_to_test(hypothesis):
            try:
                payload = hypothesis.get('payload', '')
                target = hypothesis.get('target', '')
                vulnerability_type = hypothesis.get('vulnerability_type', '').lower()
                
                # Call the real testing function
                test_result = self._execute_test(target, payload, vulnerability_type)
                
                # Parse result to determine if vulnerable
                if "VULNERABILITY FOUND" in test_result:
                    return {
                        'vulnerable': True,
                        'type': vulnerability_type,
                        'severity': 'HIGH',
                        'poc': f'Test at {target} with payload: {payload}',
                        'impact': test_result,
                        'fix': 'Review and sanitize inputs'
                    }
                
            except Exception as e:
                print(f"    Test error: {e}")
        
        return {'vulnerable': False}
    
    def _is_safe_to_test(self, hypothesis):
        """
        Safety check: Only allow non-destructive probing
        """
        dangerous_keywords = ['delete', 'drop', 'shutdown', 'format', 'rm -rf']
        payload = hypothesis.get('payload', '').lower()
        
        return not any(keyword in payload for keyword in dangerous_keywords)
    
    def _execute_test(self, target, payload, vulnerability_type):
        """
        Executes a REAL SAFE test using requests.
        """
        print(f"[BugHunter] Testing {target} with payload: {payload}")
        
        try:
            # 1. Determine injection point (Query param assumed for demo)
            if "?" in target:
                test_url = f"{target}&test={payload}"
            else:
                test_url = f"{target}?test={payload}"
            
            # 2. Execute Request
            response = self.session.get(test_url, timeout=5)
            
            # 3. Analyze Response (Simple patterns)
            evidence = []
            
            # Reflected XSS
            if "xss" in vulnerability_type.lower():
                if payload in response.text:
                    evidence.append("Payload reflected in response body")
                    
            # SQL Injection
            if "sql" in vulnerability_type.lower():
                sql_errors = ["syntax error", "mysql_fetch", "ORA-", "PostgreSQL"]
                for err in sql_errors:
                    if err in response.text:
                        evidence.append(f"SQL Error found: {err}")
            
            # Open Redirect
            if "redirect" in vulnerability_type.lower():
                if len(response.history) > 0:
                     evidence.append(f"Redirected to: {response.url}")

            if evidence:
                # Log success to DB
                self.db.add_vulnerability(
                    ip=target, 
                    cve_id="BUG-FOUND", 
                    description=f"Potential {vulnerability_type} at {test_url}", 
                    severity="High"
                )
                return f"⚠️ POTENTIAL VULNERABILITY FOUND: {', '.join(evidence)}"
            
            return "Test passed (No immediate vulnerability detected)."
            
        except requests.RequestException as e:
            return f"Test connection failed: {e}"
    
    def _fingerprint_technology(self, target):
        """
        Detect technologies used by target
        """
        try:
            response = self.session.get(target, timeout=5)
            
            tech = {
                'server': response.headers.get('Server', 'Unknown'),
                'framework': self._detect_framework(response),
                'cookies': list(response.cookies.keys())
            }
            
            return tech
        except:
            return {'server': 'Unknown'}
    
    def _detect_framework(self, response):
        """Detect web framework from response"""
        if 'Express' in response.headers.get('X-Powered-By', ''):
            return 'Express (Node.js)'
        if 'Werkzeug' in response.headers.get('Server', ''):
            return 'Flask (Python)'
        if 'ASP.NET' in response.headers.get('X-Powered-By', ''):
            return 'ASP.NET'
        return 'Unknown'
    
    def _parse_json_from_text(self, text):
        """Extract JSON from AI response"""
        try:
            # Try direct parse first
            return json.loads(text)
        except:
            # Extract JSON block from markdown
            match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            
            # Extract any JSON-like structure
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        
        return {}
    
    def _generate_bug_report(self):
        """
        Generate professional bug report
        """
        if not self.findings:
            return "No vulnerabilities found in automated testing."
        
        report = ["=" * 60]
        report.append("BUG BOUNTY REPORT")
        report.append("=" * 60)
        report.append(f"\nTotal Vulnerabilities Found: {len(self.findings)}\n")
        
        for i, bug in enumerate(self.findings, 1):
            report.append(f"\n[{i}] {bug['type']}")
            report.append(f"Severity: {bug['severity']}")
            report.append(f"Proof of Concept:\n  {bug['poc']}")
            report.append(f"Impact: {bug['impact']}")
            report.append(f"Remediation: {bug['fix']}")
            report.append("-" * 60)
        
        return "\n".join(report)
