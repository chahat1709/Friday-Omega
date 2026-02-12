import logging
import os
from datetime import datetime

def setup_logging(log_level="INFO", log_file="friday.log"):
    """
    Configure logging for the FRIDAY system.
    Creates both file and console handlers.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "."
    if log_dir != "." and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logger
    logger = logging.getLogger("FRIDAY")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler (detailed logs)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler (important messages only)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_command(agent_name, command, result, user="system"):
    """
    Log executed commands for audit trail.
    Creates a separate audit log.
    """
    audit_file = "logs/audit.log"
    os.makedirs("logs", exist_ok=True)
    
    with open(audit_file, 'a') as f:
        timestamp = datetime.now().isoformat()
        f.write(f"{timestamp} | {user} | {agent_name} | {command} | {result[:100]}\n")

def log_security_event(event_type, target, details):
    """
    Log security-related events (scans, exploits, etc.)
    """
    security_file = "logs/security.log"
    os.makedirs("logs", exist_ok=True)
    
    with open(security_file, 'a') as f:
        timestamp = datetime.now().isoformat()
        f.write(f"{timestamp} | {event_type} | {target} | {details}\n")
