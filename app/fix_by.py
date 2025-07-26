import sqlite3

conn = sqlite3.connect("users.db")
c = conn.cursor()

# Check if group_id already exists
c.execute("PRAGMA table_info(users)")
columns = [row[1] for row in c.fetchall()]
if "group_id" not in columns:
    c.execute("ALTER TABLE users ADD COLUMN group_id INTEGER;")
    print("Added group_id column to users table")
else:
    print("group_id already present, no change made.")

conn.commit()
conn.close()