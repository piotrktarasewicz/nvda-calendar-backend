import sqlite3
from fastapi import FastAPI

app = FastAPI()

DB_FILE = "nvda_calendar.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_key TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def root():
    return {"status": "nvda-backend-running-sqlite"}

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
