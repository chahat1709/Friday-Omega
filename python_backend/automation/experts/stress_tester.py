"""StressTesterExpert — Real concurrent HTTP stress testing."""
import logging
import re
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.experts.base_expert import BaseExpert
from core.llm import LLMEngine

class StressTesterExpert(BaseExpert):
    """Tier 4 Specialist: Runs REAL concurrent HTTP stress tests."""
    
    def __init__(self, llm_engine: LLMEngine):
        super().__init__("Stress Tester", llm_engine)
        self.system_prompt = "YOU ARE THE STRESS TEST WARRIOR. Saturate targets with concurrent requests."

    def execute_task(self, task_instruction: str) -> str:
        logging.info(f"[StressTester] Real stress test: {task_instruction}")
        
        # Extract target
        urls = re.findall(r'https?://\S+', task_instruction)
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', task_instruction)
        
        if urls:
            target = urls[0]
        elif ips:
            target = f"http://{ips[0]}"
        else:
            target = "http://127.0.0.1"
        
        # Parse concurrency and request count
        concurrency = 50  # default
        total_requests = 200  # default
        
        conc_match = re.search(r'(\d+)\s*(?:concurrent|threads|workers)', task_instruction)
        if conc_match: concurrency = min(int(conc_match.group(1)), 500)
        
        req_match = re.search(r'(\d+)\s*(?:requests|hits)', task_instruction)
        if req_match: total_requests = min(int(req_match.group(1)), 10000)
        
        # Execute real HTTP stress test
        try:
            import urllib.request
            
            successes = 0
            failures = 0
            response_times = []
            start_time = time.time()
            
            def hit_target(i):
                req_start = time.time()
                try:
                    req = urllib.request.Request(target, headers={'User-Agent': f'FRIDAY-StressTest/{i}'})
                    urllib.request.urlopen(req, timeout=5)
                    return time.time() - req_start, True
                except Exception:
                    return time.time() - req_start, False
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(hit_target, i) for i in range(total_requests)]
                for future in as_completed(futures):
                    duration, success = future.result()
                    response_times.append(duration)
                    if success:
                        successes += 1
                    else:
                        failures += 1
            
            total_time = time.time() - start_time
            avg_response = sum(response_times) / len(response_times) if response_times else 0
            rps = total_requests / total_time if total_time > 0 else 0
            
            output = f"""STRESS TEST COMPLETE on {target}
  Total Requests: {total_requests}
  Concurrency: {concurrency} workers
  Duration: {total_time:.2f}s
  Requests/sec: {rps:.1f}
  Success: {successes} | Failed: {failures}
  Avg Response Time: {avg_response*1000:.1f}ms
  Success Rate: {(successes/total_requests*100):.1f}%"""
            
            if failures > successes:
                output += f"\n  ⚠️ TARGET SATURATED: Failure rate exceeds 50%."
            
            return self.log_result(output)
            
        except Exception as e:
            return self.log_result(f"STRESS TEST ERROR: {e}")
