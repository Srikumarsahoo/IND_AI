import sqlite3
from datetime import datetime
import os

DB_NAME = "chat.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ========== SCHEMA SETUP ==========

def init_db():
    """Create all tables for users, groups, sessions, personal and group (co-memory) messages."""
    with get_db_connection() as conn:
        c = conn.cursor()
        # Group table
        c.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        # User table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                group_id INTEGER,
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        ''')
        # Chat sessions (per-user)
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        # Individual chat messages
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
            )
        ''')
        # Shared group memory messages
        c.execute('''
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        ''')
        conn.commit()

# ========== GROUP & USER MANAGEMENT ==========

def create_group(name: str) -> int:
    """Create a group, return its id (or get existing)."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (name,))
        conn.commit()
        c.execute("SELECT id FROM groups WHERE name = ?", (name,))
        return c.fetchone()["id"]

def get_user(username: str):
    """Fetch user row by username."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        return c.fetchone()

def get_user_by_id(user_id: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return c.fetchone()

def create_user(username: str, password: str, group_name: str) -> int:
    """Register a user and assign to a group; return user id."""
    group_id = create_group(group_name)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, group_id) VALUES (?, ?, ?)", (username, password, group_id))
        conn.commit()
        return c.lastrowid

# ========== CHAT SESSIONS & PERSONAL MESSAGES ==========

def create_chat_session(session_id: str, user_id: int, title: str = "New Chat"):
    """Create a new chat session for a user."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO chat_sessions (id, user_id, title) VALUES (?, ?, ?)", (session_id, user_id, title))
        conn.commit()

def save_message(session_id: str, role: str, content: str):
    """Save a personal message in a session (user or assistant)."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
        conn.commit()

def fetch_messages(session_id: str):
    """Fetch all messages (user/assistant) in a session."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY timestamp", (session_id,))
        return c.fetchall()

def get_chat_sessions(user_id: int):
    """Fetch all chat sessions for a user, newest first."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, title, created FROM chat_sessions WHERE user_id = ? ORDER BY created DESC", (user_id,))
        return c.fetchall()

def rename_chat_session(session_id: str, new_title: str):
    """Rename a user's chat session."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE chat_sessions SET title = ? WHERE id = ?", (new_title, session_id))
        conn.commit()

# ========== GROUP MEMORY / CO-MEMORY ==========

def save_group_message(group_id: int, role: str, content: str):
    """Save a shared group memory message."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO group_messages (group_id, role, content) VALUES (?, ?, ?)", (group_id, role, content))
        conn.commit()

def fetch_group_messages(group_id: int, limit: int = 15):
    """Fetch last N group (shared) memory messages in order."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT role, content FROM group_messages WHERE group_id = ? ORDER BY timestamp DESC LIMIT ?", (group_id, limit))
        return list(reversed(c.fetchall()))

# ========== DB RESET (DEV ONLY) ==========

def reset_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()

# --- Initialize on import ---
init_db()
