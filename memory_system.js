// Memory System for FRIDAY
// Stores conversations, preferences, and context for persistent learning

const Database = require('better-sqlite3');
const path = require('path');

class MemorySystem {
  constructor(dbPath = './friday_memory.db') {
    try {
      this.db = new Database(dbPath);
      this.db.pragma('journal_mode = WAL');
      this.initializeTables();
      console.log('[Memory System] ✅ Initialized');
    } catch (e) {
      console.error('[Memory System Error]', e.message);
      this.db = null;
    }
  }

  initializeTables() {
    // Conversations table
    this.db.exec(`
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
    `);

    // User preferences table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS user_preferences (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Tasks table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT,
        description TEXT,
        status TEXT,
        priority TEXT,
        due_date DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
      )
    `);

    // Reminders table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        message TEXT,
        due_time DATETIME,
        is_completed BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // User learning patterns
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS learning_patterns (
        pattern_id TEXT PRIMARY KEY,
        pattern_type TEXT,
        keyword TEXT,
        action TEXT,
        frequency INTEGER DEFAULT 0,
        last_used DATETIME,
        confidence REAL
      )
    `);

    // User Facts (Persistent Profile)
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS user_facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        fact TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    console.log('[Memory System] Tables initialized');
  }

  // Store a conversation
  storeConversation(sessionId, userMessage, fridayResponse, metadata = {}) {
    try {
      const id = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      const stmt = this.db.prepare(`
        INSERT INTO conversations (
          id, session_id, user_message, friday_response, 
          confidence, intent, entities, sentiment, context_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      stmt.run(
        id,
        sessionId,
        userMessage,
        fridayResponse,
        metadata.confidence || 0.8,
        metadata.intent || 'general',
        JSON.stringify(metadata.entities || {}),
        metadata.sentiment || 'neutral',
        metadata.contextKey || 'general'
      );

      console.log('[Memory] Conversation stored:', id);
      return id;
    } catch (e) {
      console.error('[Memory Error] Storing conversation:', e.message);
    }
  }

  // Retrieve conversation history
  getConversationHistory(sessionId, limit = 10) {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM conversations 
        WHERE session_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
      `);

      const conversations = stmt.all(sessionId, limit);
      return conversations.map(conv => ({
        ...conv,
        entities: JSON.parse(conv.entities || '{}')
      }));
    } catch (e) {
      console.error('[Memory Error] Retrieving history:', e.message);
      return [];
    }
  }

  // Store user preference
  setPreference(key, value) {
    try {
      const stmt = this.db.prepare(`
        INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
      `);

      stmt.run(key, typeof value === 'string' ? value : JSON.stringify(value));
      console.log('[Memory] Preference set:', key);
    } catch (e) {
      console.error('[Memory Error] Setting preference:', e.message);
    }
  }

  // Get user preference
  getPreference(key) {
    try {
      const stmt = this.db.prepare('SELECT value FROM user_preferences WHERE key = ?');
      const result = stmt.get(key);
      
      if (result) {
        try {
          return JSON.parse(result.value);
        } catch {
          return result.value;
        }
      }
      return null;
    } catch (e) {
      console.error('[Memory Error] Getting preference:', e.message);
      return null;
    }
  }

  // Create a task
  createTask(title, description = '', priority = 'medium', dueDate = null) {
    try {
      const id = `task_${Date.now()}`;
      
      const stmt = this.db.prepare(`
        INSERT INTO tasks (id, title, description, status, priority, due_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
      `);

      stmt.run(id, title, description, 'pending', priority, dueDate);
      console.log('[Memory] Task created:', id);
      return id;
    } catch (e) {
      console.error('[Memory Error] Creating task:', e.message);
    }
  }

  // Get all tasks
  getTasks(status = null) {
    try {
      let query = 'SELECT * FROM tasks';
      const params = [];

      if (status) {
        query += ' WHERE status = ?';
        params.push(status);
      }

      query += ' ORDER BY priority DESC, due_date ASC';

      const stmt = this.db.prepare(query);
      return stmt.all(...params);
    } catch (e) {
      console.error('[Memory Error] Getting tasks:', e.message);
      return [];
    }
  }

  // Complete a task
  completeTask(taskId) {
    try {
      const stmt = this.db.prepare(`
        UPDATE tasks 
        SET status = 'completed', completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
      `);

      stmt.run(taskId);
      console.log('[Memory] Task completed:', taskId);
    } catch (e) {
      console.error('[Memory Error] Completing task:', e.message);
    }
  }

  // Create a reminder
  createReminder(message, dueTime) {
    try {
      const id = `reminder_${Date.now()}`;
      
      const stmt = this.db.prepare(`
        INSERT INTO reminders (id, message, due_time, created_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
      `);

      stmt.run(id, message, dueTime);
      console.log('[Memory] Reminder created:', id);
      return id;
    } catch (e) {
      console.error('[Memory Error] Creating reminder:', e.message);
    }
  }

  // Get pending reminders
  getPendingReminders() {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM reminders 
        WHERE is_completed = 0 
        AND datetime(due_time) <= datetime('now')
        ORDER BY due_time ASC
      `);

      return stmt.all();
    } catch (e) {
      console.error('[Memory Error] Getting reminders:', e.message);
      return [];
    }
  }

  // Learn from user behavior
  recordPattern(patternType, keyword, action, confidence = 0.8) {
    try {
      const patternId = `pattern_${patternType}_${keyword}`.toLowerCase();
      
      // Check if pattern exists
      const existing = this.db.prepare('SELECT * FROM learning_patterns WHERE pattern_id = ?').get(patternId);

      if (existing) {
        const stmt = this.db.prepare(`
          UPDATE learning_patterns 
          SET frequency = frequency + 1, last_used = CURRENT_TIMESTAMP, confidence = ?
          WHERE pattern_id = ?
        `);
        stmt.run(confidence, patternId);
      } else {
        const stmt = this.db.prepare(`
          INSERT INTO learning_patterns (pattern_id, pattern_type, keyword, action, frequency, last_used, confidence)
          VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP, ?)
        `);
        stmt.run(patternId, patternType, keyword, action, confidence);
      }

      console.log('[Memory] Pattern learned:', patternId);
    } catch (e) {
      console.error('[Memory Error] Recording pattern:', e.message);
    }
  }

  // Get learned patterns
  getPatterns(patternType = null, limit = 10) {
    try {
      let query = 'SELECT * FROM learning_patterns';
      const params = [];

      if (patternType) {
        query += ' WHERE pattern_type = ?';
        params.push(patternType);
      }

      query += ' ORDER BY frequency DESC, last_used DESC LIMIT ?';
      params.push(limit);

      const stmt = this.db.prepare(query);
      return stmt.all(...params);
    } catch (e) {
      console.error('[Memory Error] Getting patterns:', e.message);
      return [];
    }
  }

  // Get tasks due within a certain timeframe (in hours)
  getUpcomingTasks(hours = 24) {
    try {
      // Calculate the cutoff time
      const now = new Date();
      const future = new Date(now.getTime() + hours * 60 * 60 * 1000);
      
      const stmt = this.db.prepare(`
        SELECT * FROM tasks 
        WHERE status != 'completed' 
        AND due_date IS NOT NULL 
        AND due_date BETWEEN ? AND ?
        ORDER BY due_date ASC
      `);
      
      return stmt.all(now.toISOString(), future.toISOString());
    } catch (e) {
      console.error('[Memory Error] Getting upcoming tasks:', e.message);
      return [];
    }
  }

  // Get memory stats
  getStats() {
    try {
      const conversations = this.db.prepare('SELECT COUNT(*) as count FROM conversations').get();
      const tasks = this.db.prepare('SELECT COUNT(*) as count FROM tasks').get();
      const reminders = this.db.prepare('SELECT COUNT(*) as count FROM reminders').get();
      const patterns = this.db.prepare('SELECT COUNT(*) as count FROM learning_patterns').get();

      return {
        conversations: conversations.count,
        tasks: tasks.count,
        reminders: reminders.count,
        patterns: patterns.count
      };
    } catch (e) {
      console.error('[Memory Error] Getting stats:', e.message);
      return {};
    }
  }

  // Close database
  close() {
    try {
      if (this.db) {
        this.db.close();
        console.log('[Memory System] Closed');
      }
    } catch (e) {
      console.error('[Memory Error] Closing:', e.message);
    }
  }
}

module.exports = MemorySystem;
