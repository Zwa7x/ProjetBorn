# scripts/init_db.py
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "settings.db"
SQL_FILE = BASE_DIR / "sql" / "tables.sql"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
    conn.close()
    print(f"Initialized DB at {DB_PATH}")

if __name__ == "__main__":
    init_db()
