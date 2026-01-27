import sqlite3
from datetime import datetime

DB_NAME = "database.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # ================= USERS TABLE =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # ================= KEYS TABLE =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        hwid TEXT,
        days INTEGER
    )
    """)

    # ================= LOGS TABLE (NEW) =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        ip TEXT,
        created_at TEXT
    )
    """)

    # ================= FIX OLD DATABASES =================
    try:
        c.execute("ALTER TABLE keys ADD COLUMN days INTEGER DEFAULT 30")
    except:
        pass

    # ================= CREATE DEFAULT ADMIN =================
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "123456", "admin")
        )

    conn.commit()
    conn.close()


# ================= LOG HELPER FUNCTION =================
def add_log(username, action, ip):
    conn = get_db()
    c = conn.cursor()

    c.execute(
        "INSERT INTO logs (username, action, ip, created_at) VALUES (?, ?, ?, ?)",
        (username, action, ip, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()
