import os
import psycopg
from fastapi import FastAPI

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/")
def root():
    return {
        "status": "nvda-backend-running",
        "database_url_present": DATABASE_URL is not None
    }

@app.get("/db-test")
def db_test():
    if not DATABASE_URL:
        return {"db": "error", "details": "DATABASE_URL missing"}

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()
        return {"db": "connected", "result": result[0]}
    except Exception as e:
        return {"db": "error", "details": str(e)}
