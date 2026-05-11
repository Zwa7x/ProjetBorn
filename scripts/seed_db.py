# scripts/seed_db.py
import pandas as pd
import sqlite3
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "settings.db"

def upsert_region(cur, acronym, long_name):
    cur.execute("""
    INSERT INTO regions(acronym,long_name) VALUES(?,?)
    ON CONFLICT(acronym) DO UPDATE SET long_name=excluded.long_name
    """, (acronym, long_name))

def insert_place(cur, name, region_acronym, address):
    cur.execute("""
    INSERT INTO places(name,region_acronym,address) VALUES(?,?,?)
    """, (name, region_acronym, address))

def upsert_charger(cur, code, label, specs):
    cur.execute("""
    INSERT INTO charger_types(code,label,specs) VALUES(?,?,?)
    ON CONFLICT(code) DO UPDATE SET label=excluded.label, specs=excluded.specs
    """, (code, label, json.dumps(specs)))

def seed_from_excel(path):
    xls = pd.ExcelFile(path)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if 'Regions' in xls.sheet_names:
        df = pd.read_excel(xls, 'Regions').fillna('')
        for _, r in df.iterrows():
            ac = str(r.get('acronym','')).strip()
            ln = str(r.get('long_name') or ac).strip()
            if ac:
                upsert_region(cur, ac, ln)
    if 'Places' in xls.sheet_names:
        df = pd.read_excel(xls, 'Places').fillna('')
        for _, p in df.iterrows():
            name = str(p.get('name','')).strip()
            region = str(p.get('region_acronym','')).strip()
            addr = str(p.get('address','')).strip()
            if name and region:
                insert_place(cur, name, region, addr)
    if 'Chargers' in xls.sheet_names:
        df = pd.read_excel(xls, 'Chargers').fillna('')
        for _, c in df.iterrows():
            code = str(c.get('code','')).strip()
            label = str(c.get('label') or code).strip()
            specs = c.get('specs') or {}
            upsert_charger(cur, code, label, specs)
    conn.commit()
    conn.close()
    print("Seed complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_db.py path/to/initial_data.xlsx")
        sys.exit(1)
    seed_from_excel(sys.argv[1])
