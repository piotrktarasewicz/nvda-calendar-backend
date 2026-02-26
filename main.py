# -*- coding: UTF-8 -*-

import os
import sqlite3
import secrets
from datetime import datetime, timedelta, date
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

DB_FILE = "calendar.db"

WEEKDAYS_PL = [
    "poniedziałek",
    "wtorek",
    "środa",
    "czwartek",
    "piątek",
    "sobota",
    "niedziela"
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

    time_text = start_dt.strftime("%H:%M")

    # Dziś / jutro / pojutrze
    if offset == 0:
        day_prefix = ""
    elif offset == 1:
        day_prefix = ""
    elif offset == 2:
        day_prefix = ""
    else:
        weekday = WEEKDAYS_PL[start_dt.weekday()]
        month = MONTHS_PL[start_dt.month - 1]
        day_prefix = f"W {weekday}, {start_dt.day} {month}, "

    status = ""
    if start_dt <= now <= end_dt:
        status = " trwa,"

    return f"{day_prefix}o {time_text},{status} {title}"


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

        # przyszłe lub trwające
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
        ("Spotkanie trwające", now - timedelta(minutes=30), now + timedelta(minutes=30)),
        ("Spotkanie później", now + timedelta(hours=2), now + timedelta(hours=3)),
        ("Jutro rano", now + timedelta(days=1, hours=1), now + timedelta(days=1, hours=2)),
        ("Za trzy dni", now + timedelta(days=3, hours=1), now + timedelta(days=3, hours=2)),
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
