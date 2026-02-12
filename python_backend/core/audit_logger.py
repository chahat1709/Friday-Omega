import logging
import json
import os
from datetime import datetime
import hashlib

class AuditLogger:
    """
    Cryptographic audit log.
    Ensures non-repudiation of all authorized cyber actions.
    """
    def __init__(self, log_dir="logs/security"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl")
        self.last_hash = "0" * 64 # Genesis hash
        
        # Recover last hash from file if it exists
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = json.loads(lines[-1].strip())
                        self.last_hash = last_line.get("hash", "0" * 64)
            except Exception as e:
                logging.error(f"AuditLogger: Could not recover last hash: {e}")

    def log_action(self, operator, agent, tool, target, status):
        """
        Writes a chain-hashed log entry (Immutability).
        Each entry's hash includes the hash of the previous entry.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operator": operator,
            "agent": agent,
            "tool": tool,
            "target": target,
            "status": status,
            "prev_hash": self.last_hash
        }
        
        # Chain hash: sha256(current_entry + previous_hash)
        entry_str = json.dumps(entry, sort_keys=True)
        entry_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        
        log_entry = {
            "hash": entry_hash,
            "record": entry
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        self.last_hash = entry_hash # Update for next log
        logging.info(f"AuditLogger: Action {status} cryptographically chained -> {entry_hash[:8]}...")
