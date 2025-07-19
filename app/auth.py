import bcrypt
import sqlite3
from itsdangerous import URLSafeSerializer

DB_FILE = "users.db"
SECRET_KEY = "supersecretkey"  # You can make this more secure
serializer = URLSafeSerializer(SECRET_KEY)

# Init DB (run once)
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )''')
        conn.commit()

def register_user(username, password):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
        return True
    except:
        return False

def verify_user(username, password):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        if row and bcrypt.checkpw(password.encode(), row[0].encode()):
            return True
    return False

def create_session(username):
    return serializer.dumps({"user": username})

def decode_session(token):
    try:
        data = serializer.loads(token)
        return data["user"]
    except:
        return None
