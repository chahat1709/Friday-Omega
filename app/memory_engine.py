import sqlite3
import json
import os
from datetime import datetime, timedelta

class MemoryEngine:
    def __init__(self, db_path="friday_memory.db"):
        # Ensure absolute path if needed, or rely on CWD
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._init_db()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency with Node.js
            self.conn.execute("PRAGMA journal_mode=WAL;")
        except Exception as e:
            print(f"[Memory Error] Connection failed: {e}")

    def _init_db(self):
        """Initialize SQL tables if they don't exist."""
        if not self.conn: return
        cursor = self.conn.cursor()
        
        # Ensure conversations table exists (compatible with Node.js schema)
        # Node.js schema: id, session_id, timestamp, user_message, friday_response, confidence, intent, entities, sentiment, context_key
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_message TEXT,
                friday_response TEXT,
                confidence REAL,
                intent TEXT,
                entities TEXT,
                sentiment TEXT,
                context_key TEXT
            )
        ''')

        # New table for Temporal Events (The "Brain" feature)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temporal_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT,
                event_date DATETIME,
                status TEXT DEFAULT 'pending', -- pending, reminded, completed
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # New table for User Facts (Persistent Profile)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT, -- personal, work, preference, relationship
                fact TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # New table for Visual Logs (Spy Mode)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visual_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def log_visual_observation(self, description):
        """Log a visual observation from the camera."""
        if not self.conn: return
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO visual_logs (description) VALUES (?)", (description,))
        self.conn.commit()

    def get_recent_context(self, limit=5):
        """Get recent conversation history for the LLM context."""
        if not self.conn: return []
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT user_message, friday_response 
            FROM conversations 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        # Return in chronological order (oldest first)
        history = []
        for row in reversed(rows):
            history.append({"role": "user", "content": row["user_message"]})
            history.append({"role": "model", "content": row["friday_response"]})
        return history

    def add_user_fact(self, category, fact):
        """Add a permanent fact about the user."""
        if not self.conn: return
        cursor = self.conn.cursor()
        # Check if fact already exists to avoid duplicates
        cursor.execute("SELECT id FROM user_facts WHERE fact = ?", (fact,))
        if cursor.fetchone():
            return # Already exists
            
        cursor.execute(
            "INSERT INTO user_facts (category, fact) VALUES (?, ?)", 
            (category, fact)
        )
        self.conn.commit()

    def get_user_profile(self):
        """Get all user facts formatted as a string context."""
        if not self.conn: return ""
        cursor = self.conn.cursor()
        cursor.execute("SELECT category, fact FROM user_facts ORDER BY category")
        rows = cursor.fetchall()
        
        if not rows:
            return "No specific user details known yet."
            
        profile_text = "KNOWN USER FACTS:\n"
        for row in rows:
            profile_text += f"- [{row['category'].upper()}] {row['fact']}\n"
        return profile_text

    def add_temporal_event(self, event_name, date_obj):
        """Log a future event."""
        if not self.conn: return
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO temporal_events (event_name, event_date) VALUES (?, ?)", 
            (event_name, date_obj.isoformat())
        )
        self.conn.commit()

    def check_temporal_triggers(self):
        """
        Check for events relevant to TODAY or RECENT PAST.
        Returns a string context to inject into the prompt.
        """
        if not self.conn: return ""
        
        today = datetime.now().date()
        cursor = self.conn.cursor()
        
        # Get pending events
        cursor.execute("SELECT id, event_name, event_date FROM temporal_events WHERE status='pending'")
        events = cursor.fetchall()
        
        triggers = []
        for row in events:
            eid = row["id"]
            name = row["event_name"]
            try:
                # Handle ISO format string
                event_dt = datetime.fromisoformat(row["event_date"])
                event_date = event_dt.date()
            except:
                continue

            if event_date == today:
                triggers.append(f"User has '{name}' TODAY. Wish them luck or ask about it.")
                # We don't mark as completed yet, maybe remind once
                cursor.execute("UPDATE temporal_events SET status='reminded' WHERE id=?", (eid,))
            
            elif event_date < today:
                # Past event
                triggers.append(f"User had '{name}' on {event_date}. Ask: 'How was the {name}?'")
                cursor.execute("UPDATE temporal_events SET status='completed' WHERE id=?", (eid,))
        
        self.conn.commit()
        return " ".join(triggers)

    def close(self):
        if self.conn:
            self.conn.close()
