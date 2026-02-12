import sqlite3
import json
import os
from datetime import datetime

class DatabaseManager:
    """
    Manages persistent storage for scan results, vulnerabilities, and logs.
    """
    def __init__(self, db_path="friday_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Devices table
        c.execute('''CREATE TABLE IF NOT EXISTS devices (
            ip TEXT PRIMARY KEY,
            hostname TEXT,
            last_seen DATETIME,
            os TEXT,
            status TEXT
        )''')
        
        # Open Ports table
        c.execute('''CREATE TABLE IF NOT EXISTS open_ports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            port INTEGER,
            service TEXT,
            version TEXT,
            last_scanned DATETIME,
            FOREIGN KEY (ip) REFERENCES devices (ip)
        )''')
        
        # Vulnerabilities table
        c.execute('''CREATE TABLE IF NOT EXISTS vulnerabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            cve_id TEXT,
            description TEXT,
            severity TEXT,
            status TEXT,
            detected_at DATETIME
        )''')
        
        conn.commit()
        conn.close()

    def add_device(self, ip, hostname="Unknown"):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO devices (ip, hostname, last_seen, status)
                     VALUES (?, ?, ?, ?)''', (ip, hostname, datetime.now(), "active"))
        conn.commit()
        conn.close()

    def add_port(self, ip, port, service="Unknown", version=""):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Check if exists
        c.execute('SELECT id FROM open_ports WHERE ip=? AND port=?', (ip, port))
        row = c.fetchone()
        if row:
            c.execute('UPDATE open_ports SET last_scanned=?, service=?, version=? WHERE id=?',
                      (datetime.now(), service, version, row[0]))
        else:
            c.execute('''INSERT INTO open_ports (ip, port, service, version, last_scanned)
                         VALUES (?, ?, ?, ?, ?)''', (ip, port, service, version, datetime.now()))
        conn.commit()
        conn.close()

    def add_vulnerability(self, ip, cve_id, description, severity):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO vulnerabilities (ip, cve_id, description, severity, status, detected_at)
                     VALUES (?, ?, ?, ?, ?, ?)''', 
                  (ip, cve_id, description, severity, "open", datetime.now()))
        conn.commit()
        conn.close()

    def get_device_summary(self, ip):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM devices WHERE ip=?', (ip,))
        device = c.fetchone()
        
        c.execute('SELECT port, service FROM open_ports WHERE ip=?', (ip,))
        ports = c.fetchall()
        
        c.execute('SELECT cve_id, severity FROM vulnerabilities WHERE ip=?', (ip,))
        vulns = c.fetchall()
        
        conn.close()
        
        if not device:
            return None
            
        return {
            "ip": device[0],
            "ports": [{"port": p[0], "service": p[1]} for p in ports],
            "vulnerabilities": [{"cve": v[0], "severity": v[1]} for v in vulns]
        }
