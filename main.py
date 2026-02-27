# -*- coding: UTF-8 -*-

import sqlite3
import secrets
from datetime import datetime, timedelta, date
from fastapi import FastAPI

app = FastAPI()

DB_FILE = "calendar.db"

WEEKDAYS_PL = [
    "poniedziałek",
    "wtorek",
    "środę",
    "czwartek",
    "piątek",
    "sobotę",
    "niedzielę"
]

MONTHS_PL = [
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia"
]


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_key TEXT PRIMARY KEY,
                created_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_key TEXT,
                title TEXT,
                start_time TEXT,
                end_time TEXT
            )
        """)
        conn.commit()


init_db()


def format_event(title, start_iso, end_iso, offset):
    start_dt = datetime.fromisoformat(start_iso)
    end_dt = datetime.fromisoformat(end_iso)
    now = datetime.now()

    start_time_text = start_dt.strftime("%H:%M")
    end_time_text = end_dt.strftime("%H:%M")

    # Prefiks dnia
    if offset == 0:
        prefix = "Dziś "
    elif offset == 1:
        prefix = "Jutro "
    elif offset == 2:
        prefix = "Pojutrze "
    else:
        weekday = WEEKDAYS_PL[start_dt.weekday()]
        month = MONTHS_PL[start_dt.month - 1]
        prefix = f"W {weekday}, {start_dt.day} {month} "

    # Jeśli trwa (tylko sensowne dla dziś)
    if offset == 0 and start_dt <= now <= end_dt:
        return f"Dziś trwa {title} do {end_time_text}"

    # Standardowy format
    return f"{prefix}o {start_time_text} {title}"


@app.get("/")
def root():
    return {"status": "nvda-backend-running-sqlite"}


@app.post("/register")
def register():
    user_key = secrets.token_hex(16)
    created_at = datetime.now().isoformat()

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (user_key, created_at) VALUES (?, ?)",
            (user_key, created_at)
        )
        conn.commit()

    return {"user_key": user_key}


@app.get("/events/today/{user_key}")
def get_today(user_key: str):
    now = datetime.now()
    today = date.today()

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT title, start_time, end_time
            FROM events
            WHERE user_key = ?
        """, (user_key,))
        rows = c.fetchall()

    result = []

    for title, start_iso, end_iso in rows:
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso)

        if start_dt.date() != today:
            continue

        if start_dt >= now or (start_dt <= now <= end_dt):
            result.append(format_event(title, start_iso, end_iso, 0))

    result.sort()
    return {"events": result}


@app.get("/events/day-offset/{user_key}/{offset}")
def get_by_offset(user_key: str, offset: int):
    target_date = date.today() + timedelta(days=offset)

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT title, start_time, end_time
            FROM events
            WHERE user_key = ?
        """, (user_key,))
        rows = c.fetchall()

    result = []

    for title, start_iso, end_iso in rows:
        start_dt = datetime.fromisoformat(start_iso)

        if start_dt.date() == target_date:
            result.append(format_event(title, start_iso, end_iso, offset))

    result.sort()
    return {"events": result}


@app.post("/add-test-events/{user_key}")
def add_test_events(user_key: str):
    now = datetime.now()

    test_events = [
        ("Spotkanie", now - timedelta(minutes=30), now + timedelta(minutes=30)),
        ("Rozmowa z klientem", now + timedelta(hours=2), now + timedelta(hours=3)),
        ("Lekarz", now + timedelta(days=1, hours=1), now + timedelta(days=1, hours=2)),
        ("Planowanie projektu", now + timedelta(days=3, hours=1), now + timedelta(days=3, hours=2)),
    ]

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        for title, start_dt, end_dt in test_events:
            c.execute("""
                INSERT INTO events (user_key, title, start_time, end_time)
                VALUES (?, ?, ?, ?)
            """, (
                user_key,
                title,
                start_dt.isoformat(),
                end_dt.isoformat()
            ))
        conn.commit()

    return {"status": "test events added"}
