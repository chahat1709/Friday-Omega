import logging
import sys

class ApprovalGate:
    """
    Human-In-The-Loop Approval Gate.
    Pauses execution and prompts the physical operator on the terminal to authorize.
    """
    def __init__(self):
        pass

    def request_approval(self, agent_name, tool_name, target, intent):
        """
        Blocks and asks for human confirmation via CLI.
        Returns: "AUTHORIZE", "REJECT", or "DRYRUN"
        """
        print("\n" + "="*50)
        print("🛑 ACTION AUTHORIZATION REQUIRED 🛑")
        print("="*50)
        print(f"Agent:  {agent_name}")
        print(f"Action: {tool_name}")
        print(f"Target: {target}")
        print(f"Reason: {intent}")
        print("="*50)
        
        while True:
            # Note: In a UI, this would push an event to the frontend.
            # For the CLI backend, we use input().
            sys.stdout.write(f"\nDo you explicitly authorize this physical/digital action? (YES/NO/DRYRUN): ")
            sys.stdout.flush()
            choice = input().strip().upper()
            
            if choice == "YES":
                logging.info(f"ApprovalGate: Operator AUTHORIZED {tool_name} on {target}.")
                return "AUTHORIZE"
            elif choice == "NO":
                logging.warning(f"ApprovalGate: Operator REJECTED {tool_name} on {target}.")
                return "REJECT"
            elif choice == "DRYRUN":
                logging.info(f"ApprovalGate: Operator requested DRYRUN for {tool_name} on {target}.")
                return "DRYRUN"
            else:
                print("Invalid input. Please type exactly 'YES', 'NO', or 'DRYRUN'.")
