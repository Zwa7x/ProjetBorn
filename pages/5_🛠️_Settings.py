# debug_top.py — coller au tout début de pages/5_🛠️_Settings.py
import streamlit as st, traceback
try:
    # import original (laisse tel quel si tu veux tester l'import depuis utils)
    from utils import load_settings, save_settings
except Exception as e:
    st.error("Erreur d'import utils : " + str(e))
    st.text(traceback.format_exc())
    # stoppe l'exécution pour éviter comportements étranges
    st.stop()


# utils/settings_loader.py  -- SQLite version
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "settings.db"

DEFAULT_SETTINGS = {"regions": {}, "types_borne": []}

def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def _get_conn():
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)  # autocommit off; use transactions
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db(schema_sql: str):
    conn = _get_conn()
    conn.executescript(schema_sql)
    conn.close()

def load_settings() -> Dict[str, Any]:
    conn = _get_conn()
    cur = conn.cursor()
    # regions
    cur.execute("SELECT acronym, long_name FROM regions")
    regs = {}
    for row in cur.fetchall():
        regs[row["acronym"]] = {"acronyme": row["acronym"], "lieux": []}
    # places -> attach to regions by acronym
    cur.execute("SELECT name, region_acronym FROM places")
    for row in cur.fetchall():
        ra = row["region_acronym"]
        if ra not in regs:
            regs[ra] = {"acronyme": ra, "lieux": []}
        regs[ra]["lieux"].append(row["name"])
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
    """
    Overwrites DB content from settings dict.
    This is simple and safe because it uses a transaction.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        # clear tables
        cur.execute("DELETE FROM places")
        cur.execute("DELETE FROM regions")
        cur.execute("DELETE FROM charger_types")
        # insert regions
        for region_key, meta in (settings.get("regions") or {}).items():
            acr = meta.get("acronyme") or region_key
            long_name = region_key
            cur.execute("INSERT INTO regions(acronym,long_name) VALUES(?,?)", (acr, long_name))
            for lieu in meta.get("lieux", []) or []:
                cur.execute("INSERT INTO places(name,region_acronym,address) VALUES(?,?,?)", (lieu, acr, ""))
        # insert charger types (if list of strings, convert)
        for t in settings.get("types_borne", []) or []:
            if isinstance(t, str):
                code = t
                label = t
                specs = {}
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
