import sqlite3

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

    # ================= FIX OLD DATABASES =================
    # لو جدول keys اتعمل قبل كده بدون عمود days
    try:
        c.execute("ALTER TABLE keys ADD COLUMN days INTEGER DEFAULT 30")
    except:
        pass  # العمود موجود بالفعل

    # ================= CREATE DEFAULT ADMIN =================
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "123456", "admin")
        )

    conn.commit()
    conn.close()
