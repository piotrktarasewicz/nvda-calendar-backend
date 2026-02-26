import sqlite3
import secrets
from datetime import datetime
from fastapi import FastAPI, HTTPException

app = FastAPI()

DB_FILE = "nvda_calendar.db"


# --- INIT DB ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_key TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_key TEXT NOT NULL,
            title TEXT NOT NULL,
            event_time TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# --- ROOT ---
@app.get("/")
def root():
    return {"status": "nvda-backend-running"}


# --- HEALTH ---
@app.get("/health")
def health():
    return {"status": "ok"}


# --- REGISTER USER ---
@app.post("/register")
def register_user():
    user_key = secrets.token_hex(16)
    created_at = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (user_key, created_at) VALUES (?, ?)",
        (user_key, created_at)
    )

    conn.commit()
    conn.close()

    return {"user_key": user_key}


# --- GET USER ---
@app.get("/me/{user_key}")
def get_user(user_key: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_key, created_at FROM users WHERE user_key = ?",
        (user_key,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_key": row[0],
        "created_at": row[1]
    }


# --- ADD TEST EVENTS ---
@app.post("/add-test-events/{user_key}")
def add_test_events(user_key: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # sprawdzamy czy user istnieje
    cursor.execute("SELECT id FROM users WHERE user_key = ?", (user_key,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    test_events = [
        ("Spotkanie z zespołem", "2026-03-01T10:00:00"),
        ("Wizyta u lekarza", "2026-03-02T15:30:00"),
        ("Koncert w ciemności", "2026-03-05T19:00:00"),
    ]

    for title, event_time in test_events:
        cursor.execute(
            "INSERT INTO events (user_key, title, event_time) VALUES (?, ?, ?)",
            (user_key, title, event_time)
        )

    conn.commit()
    conn.close()

    return {"status": "test events added"}


# --- GET EVENTS ---
@app.get("/events/{user_key}")
def get_events(user_key: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, event_time FROM events WHERE user_key = ? ORDER BY event_time",
        (user_key,)
    )

    rows = cursor.fetchall()
    conn.close()

    events = [
        {"title": row[0], "event_time": row[1]}
        for row in rows
    ]

    return {"events": events}


# --- DB TEST ---
@app.get("/db-test")
def db_test():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        conn.close()
        return {"db": "connected", "result": result[0]}
    except Exception as e:
        return {"db": "error", "details": str(e)}
