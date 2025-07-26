import bcrypt
import sqlite3
from itsdangerous import URLSafeSerializer

DB_FILE = "users.db"
SECRET_KEY = "supersecretkey"  # Replace with a secure key in production
serializer = URLSafeSerializer(SECRET_KEY)


# ----- Initialize user and group tables -----
def init_db():
    """Create the groups and users tables if they don't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Groups table (for team/group-based features)
        c.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')
        # Users table, supports optional group_id foreign key
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                group_id INTEGER,
                FOREIGN KEY(group_id) REFERENCES groups(id)
            )
        ''')
        conn.commit()


# ----- Create or get a group id by name -----
def get_or_create_group(group_name):
    """Return existing group id by name, or create a new group and return its id."""
    if not group_name:
        return None
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM groups WHERE name = ?", (group_name,))
        row = c.fetchone()
        if row:
            return row[0]
        c.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
        conn.commit()
        return c.lastrowid


# ----- Register a user, optionally assign to a group -----
def register_user(username, password, group_name=None):
    """
    Registers a new user with a hashed password and optional group assignment.
    Returns True if successful, False if username already exists.
    """
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    group_id = get_or_create_group(group_name) if group_name else None
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (username, password, group_id) VALUES (?, ?, ?)",
                (username, hashed_pw, group_id)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists


# ----- Verify user credentials, return session dict -----
def verify_user(username, password):
    """
    Verify user credentials.
    Returns a user dict (username and group_id) if valid, else None.
    """
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT password, group_id FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        if row and bcrypt.checkpw(password.encode(), row[0].encode()):
            return {"username": username, "group_id": row[1]}
    return None


# ----- Create a secure session token -----
def create_session(user_data: dict):
    """Generate a signed session token for a user."""
    return serializer.dumps(user_data)  # e.g., {"username": "...", "group_id": 1}


# ----- Decode the session token safely -----
def decode_session(token):
    """Decode and verify session token, returns user data or None."""
    try:
        return serializer.loads(token)
    except Exception:
        return None


# ----- Get numeric user id by username -----
def get_user_id(username):
    """Get the user ID from the database given the username."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        return row[0] if row else None
