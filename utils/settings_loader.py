# utils/settings_loader.py
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "settings.db"   # <-- défini ici, avant toute utilisation

DEFAULT_SETTINGS = {"regions": {}, "types_borne": []}

def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def _get_conn():
    _ensure_data_dir()
    # crée le fichier DB si absent (connexion crée le fichier)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

# initialisation minimale du schéma si nécessaire
def init_db_if_missing():
    if not DB_PATH.exists():
        schema = """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS regions (
          acronym TEXT PRIMARY KEY,
          long_name TEXT NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS places (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          region_acronym TEXT NOT NULL,
          address TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(region_acronym) REFERENCES regions(acronym) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS charger_types (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          code TEXT UNIQUE NOT NULL,
          label TEXT NOT NULL,
          specs TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn = _get_conn()
        conn.executescript(schema)
        conn.close()

def load_settings() -> Dict[str, Any]:
    init_db_if_missing()
    conn = _get_conn()
    cur = conn.cursor()
    # regions
    cur.execute("SELECT acronym, long_name FROM regions")
    regs = {}
    for row in cur.fetchall():
        key = row["long_name"] or row["acronym"]
        regs[key] = {"acronyme": row["acronym"], "lieux": []}
    # places -> attach to regions by acronym
    cur.execute("SELECT name, region_acronym FROM places")
    for row in cur.fetchall():
        ra = row["region_acronym"]
        # find region key by matching acronym, fallback to acronym as key
        found = None
        for k, v in regs.items():
            if v.get("acronyme") == ra:
                found = k; break
        if not found:
            found = ra
            regs.setdefault(found, {"acronyme": ra, "lieux": []})
        regs[found]["lieux"].append(row["name"])
    # charger types
    cur.execute("SELECT code, label, specs FROM charger_types")
    types = []
    for row in cur.fetchall():
        try:
            specs = json.loads(row["specs"]) if row["specs"] else {}
        except Exception:
            specs = {}
        types.append({"code": row["code"], "label": row["label"], "specs": specs})
    conn.close()
    return {"regions": regs, "types_borne": types}

def save_settings(settings: Dict[str, Any]) -> None:
    init_db_if_missing()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("DELETE FROM places")
        cur.execute("DELETE FROM regions")
        cur.execute("DELETE FROM charger_types")
        # insert regions and places
        for region_key, meta in (settings.get("regions") or {}).items():
            acr = meta.get("acronyme") or region_key
            long_name = region_key
            cur.execute("INSERT INTO regions(acronym,long_name) VALUES(?,?)", (acr, long_name))
            for lieu in meta.get("lieux", []) or []:
                cur.execute("INSERT INTO places(name,region_acronym,address) VALUES(?,?,?)", (lieu, acr, ""))
        # insert charger types
        for t in settings.get("types_borne", []) or []:
            if isinstance(t, str):
                code = t; label = t; specs = {}
            elif isinstance(t, dict):
                code = t.get("code") or t.get("label") or ""
                label = t.get("label") or code
                specs = t.get("specs") or {}
            else:
                continue
            cur.execute("INSERT INTO charger_types(code,label,specs) VALUES(?,?,?)", (code, label, json.dumps(specs)))
        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        raise
    finally:
        conn.close()
