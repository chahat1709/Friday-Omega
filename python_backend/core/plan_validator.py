import logging
import json
from typing import Dict, Any, Tuple
from core.llm import LLMEngine

class PlanValidator:
    """
    Tier 1 Strategic Command: The "Chief Risk Officer".
    Maker-Checker Process: Validates the CEO's plan using an independent LLM call.
    Ensures adherence to Rules of Engagement (ROE) and safety protocols.
    """
    
    def __init__(self, llm_engine: LLMEngine):
        self.llm = llm_engine
        self.system_prompt = """
        YOU ARE THE CHIEF RISK OFFICER (PLAN VALIDATOR) FOR FRIDAY OMEGA.
        Your job is to act as a second, independent check on the CEO's mission plans.
        
        RULES OF ENGAGEMENT (ROE):
        1. NO destructive actions on unauthorized targets.
        2. NO data exfiltration unless explicitly requested.
        3. NO actions that could cause physical harm or permanent damage.
        4. ALL tools used must be in the authorized list: nmap, sqlmap, hydra, nikto, whois, shodan, etc.
        
        INPUT: A JSON mission plan from the CEO.
        OUTPUT: JSON only.
        Format:
        {
            "approved": true/false,
            "risk_score": 0-10,
            "concerns": ["Any safety or ROE violations found"],
            "recommendations": "How to fix the plan if rejected"
        }
        """

    def validate_plan(self, plan: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates a proposed mission plan.
        Returns (is_approved, validation_report)
        """
        logging.info("[PlanValidator] Assessing mission plan for safety...")
        
        prompt = f"PLEASE VALIDATE THIS MISSION PLAN:\n{json.dumps(plan, indent=2)}"
        
        try:
            response = self.llm.generate(
                system_prompt=self.system_prompt,
                prompt=prompt,
                temperature=0.0 # High precision, low creativity
            )
            
            # Robust JSON extraction
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1:
                result = json.loads(response[start_idx:end_idx+1])
                approved = result.get("approved", False)
                risk_score = result.get("risk_score", 10)
                
                if approved and risk_score < 7:
                    logging.info(f"[PlanValidator] Plan APPROVED (Risk: {risk_score}/10)")
                    return True, result
                else:
                    logging.warning(f"[PlanValidator] Plan REJECTED (Risk: {risk_score}/10). Concerns: {result.get('concerns')}")
                    return False, result
                    
        except Exception as e:
            logging.error(f"[PlanValidator] Error during validation: {e}")
            return False, {"error": str(e), "approved": False}
            
        return False, {"error": "Validation failed to produce result", "approved": False}
