# utils/data_loader.py
import os
import sqlite3
from pathlib import Path
import pandas as pd
import hashlib
import json
import shutil
import datetime
from typing import Dict, Optional

# --- Chemin DB configurable et persistant ---
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT / "data"
DATA_DIR = Path(os.environ.get("APP_DATA_DIR", str(DEFAULT_DATA_DIR)))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "app_data.db"

# --- Helpers ---
def _connect():
    # sqlite3 connection; file DB_PATH
    return sqlite3.connect(str(DB_PATH), timeout=30)

def _row_hash(row: pd.Series) -> str:
    s = json.dumps(row.fillna("").to_dict(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def _prepare_table_name(sheet_name: str) -> str:
    return "sheet_" + "".join(c if c.isalnum() else "_" for c in sheet_name).lower()

# --- Ingestion avec imports_log ---
def ingest_excel(excel_path: str,
                 mapping: Optional[Dict[str, Dict[str, str]]] = None,
                 sheets: Optional[list] = None,
                 mode: str = "upsert"):
    """
    Ingest Excel into SQLite and log the import.
    Returns a summary dict: { sheet_name: {rows_total, inserted}, ... }
    Also writes one row per sheet into imports_log(import_id, source_file, ts, sheet_name, rows_total, inserted).
    mode: "upsert" or "replace"
    """
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"{excel_path} not found")

    xls = pd.read_excel(excel_path, sheet_name=None, dtype=str)
    to_process = sheets or list(xls.keys())

    conn = _connect()
    summary = {}
    try:
        cur = conn.cursor()
        # ensure imports_log exists
        cur.execute('''
            CREATE TABLE IF NOT EXISTS imports_log (
                import_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT,
                ts TEXT,
                sheet_name TEXT,
                rows_total INTEGER,
                inserted INTEGER
            );
        ''')
        conn.commit()

        for sheet in to_process:
            if sheet not in xls:
                continue
            df = xls[sheet].copy()
            if mapping and sheet in mapping:
                df = df.rename(columns=mapping[sheet])

            # normalize column names
            df.columns = [str(c).strip() for c in df.columns]
            df.columns = ["".join(ch if ch.isalnum() or ch=='_' else '_' for ch in str(c)).lower() for c in df.columns]

            table = _prepare_table_name(sheet)
            df["_row_hash"] = df.apply(_row_hash, axis=1)

            # create table if needed
            if mode == "replace":
                cur.execute(f'DROP TABLE IF EXISTS "{table}"')
                conn.commit()

            cols_sql = ", ".join([f"'{c}' TEXT" for c in df.columns if c != "_row_hash"])
            create_sql = f'''
                CREATE TABLE IF NOT EXISTS "{table}" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {cols_sql},
                    _row_hash TEXT,
                    UNIQUE(_row_hash)
                );
            '''
            cur.execute(create_sql)
            conn.commit()

            inserted = 0
            if mode == "replace":
                # replace entire table
                df.to_sql(table, conn, if_exists="append", index=False)
                inserted = len(df)
            else:
                # upsert by _row_hash: insert only new hashes
                cur.execute(f'SELECT _row_hash FROM "{table}"')
                existing_hashes = set(r[0] for r in cur.fetchall() if r[0] is not None)
                new_rows = df[~df["_row_hash"].isin(existing_hashes)].copy()
                if not new_rows.empty:
                    new_rows.to_sql(table, conn, if_exists="append", index=False)
                    inserted = len(new_rows)
            conn.commit()

            # log per sheet
            rows_total = len(df)
            ts = datetime.datetime.utcnow().isoformat() + "Z"
            cur.execute(
                "INSERT INTO imports_log (source_file, ts, sheet_name, rows_total, inserted) VALUES (?, ?, ?, ?, ?)",
                (str(excel_path.name), ts, sheet, rows_total, inserted)
            )
            conn.commit()

            summary[sheet] = {"rows_total": rows_total, "inserted": inserted}

    finally:
        conn.close()

    return summary

# --- Load functions ---
def load_table(table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
    table = table_name if table_name.startswith("sheet_") else _prepare_table_name(table_name)
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table,))
        if cur.fetchone() is None:
            raise ValueError(f"Table '{table}' introuvable. Ingest Excel d'abord.")
        q = f'SELECT * FROM "{table}"'
        if limit:
            q += f" LIMIT {int(limit)}"
        df = pd.read_sql_query(q, conn)
        return df
    finally:
        conn.close()

def load_all(include_internal: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Retourne toutes les tables importées.
    - include_internal=False (par défaut) exclut les tables SQLite internes (sqlite_*)
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        if not include_internal:
            tables = [t for t in tables if not t.startswith("sqlite_")]
        res = {}
        for t in tables:
            res[t] = pd.read_sql_query(f'SELECT * FROM "{t}"', conn)
        return res
    finally:
        conn.close()

# --- Save / upsert table from DataFrame ---
def save_table_upsert(table_name: str, df: pd.DataFrame, mode: str = "upsert"):
    table = table_name if table_name.startswith("sheet_") else _prepare_table_name(table_name)
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df.columns = ["".join(ch if ch.isalnum() or ch == '_' else '_' for ch in str(c)).lower() for c in df.columns]
    if "_row_hash" not in df.columns:
        df["_row_hash"] = df.apply(_row_hash, axis=1)
    conn = _connect()
    try:
        cur = conn.cursor()
        cols_sql = ", ".join([f"'{c}' TEXT" for c in df.columns if c != "_row_hash"])
        create_sql = f'''
            CREATE TABLE IF NOT EXISTS "{table}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {cols_sql},
                _row_hash TEXT,
                UNIQUE(_row_hash)
            );
        '''
        cur.execute(create_sql)
        conn.commit()
        if mode == "replace":
            cur.execute(f'DELETE FROM "{table}"')
            conn.commit()
            df.to_sql(table, conn, if_exists="append", index=False)
            conn.commit()
            return {"inserted": len(df), "skipped": 0}
        cur.execute(f'SELECT _row_hash FROM "{table}"')
        existing_hashes = set(r[0] for r in cur.fetchall() if r[0] is not None)
        new_rows = df[~df["_row_hash"].isin(existing_hashes)].copy()
        if new_rows.empty:
            return {"inserted": 0, "skipped": len(df)}
        new_rows.to_sql(table, conn, if_exists="append", index=False)
        conn.commit()
        return {"inserted": len(new_rows), "skipped": len(df) - len(new_rows)}
    finally:
        conn.close()

# --- Export / Import DB (backup / restore) ---
def export_db(dest_path: str = None) -> str:
    """
    Copie app_data.db vers dest_path (ou backups/app_data_<ts>.db si None).
    Retourne le chemin du fichier créé.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError("DB introuvable")
    if dest_path is None:
        dest_dir = DATA_DIR / "backups"
        dest_dir.mkdir(exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dest = dest_dir / f"app_data_{ts}.db"
    else:
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB_PATH, dest)
    return str(dest)

def import_db(src_path: str) -> str:
    """
    Remplace app_data.db par src_path (fichier uploadé/restauré).
    Retourne le chemin DB_PATH.
    """
    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(src)
    shutil.copy2(src, DB_PATH)
    return str(DB_PATH)
