# utils/data_loader.py
import sqlite3
from pathlib import Path
import pandas as pd
import hashlib
import json
from typing import Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "app_data.db"

def _connect():
    return sqlite3.connect(str(DB_PATH), timeout=30, isolation_level=None)  # autocommit off by default

def _row_hash(row: pd.Series) -> str:
    # stable hash of row values (stringified)
    s = json.dumps(row.fillna("").to_dict(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def _prepare_table_name(sheet_name: str) -> str:
    # safe table name
    return "sheet_" + "".join(c if c.isalnum() else "_" for c in sheet_name).lower()

def ingest_excel(
    excel_path: str,
    mapping: Optional[Dict[str, Dict[str, str]]] = None,
    sheets: Optional[list] = None,
    mode: str = "upsert"
):
    """
    Ingest Excel into SQLite.
    - excel_path: path to .xlsx
    - mapping: optional dict {sheet_name: {col_excel: col_table_name, ...}} to rename columns
    - sheets: list of sheet names to import (None = all)
    - mode: "upsert" (default) or "replace" (drop+create)
    """
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"{excel_path} not found")

    xls = pd.read_excel(excel_path, sheet_name=None, dtype=str)  # read all as str to avoid dtype surprises
    to_process = sheets or list(xls.keys())

    conn = _connect()
    cur = conn.cursor()
    try:
        for sheet in to_process:
            if sheet not in xls:
                continue
            df = xls[sheet].copy()
            # apply mapping if provided
            if mapping and sheet in mapping:
                df = df.rename(columns=mapping[sheet])

            # normalize column names: strip, replace spaces
            df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
            df.columns = [ "".join(ch if ch.isalnum() or ch=='_' else '_' for ch in str(c)).lower() for c in df.columns ]

            table = _prepare_table_name(sheet)

            # compute row hash
            df["_row_hash"] = df.apply(_row_hash, axis=1)

            if mode == "replace":
                cur.execute(f"DROP TABLE IF EXISTS {table}")
                conn.commit()

            # create table if not exists (we store everything as TEXT except _row_hash)
            cols_sql = ", ".join([f"'{c}' TEXT" for c in df.columns if c != "_row_hash"])
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS '{table}' (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {cols_sql},
                    _row_hash TEXT,
                    UNIQUE(_row_hash)
                );
            """
            cur.execute(create_sql)
            conn.commit()

            if mode == "replace":
                # bulk insert
                df.to_sql(table, conn, if_exists="append", index=False)
            else:
                # upsert by _row_hash: insert only rows whose hash not present
                existing_hashes = set(r[0] for r in cur.execute(f"SELECT _row_hash FROM '{table}'").fetchall())
                new_rows = df[~df["_row_hash"].isin(existing_hashes)].copy()
                if not new_rows.empty:
                    # write new rows
                    new_rows.to_sql(table, conn, if_exists="append", index=False)
            # commit per sheet
            conn.commit()
    finally:
        cur.close()
        conn.close()

def load_table(table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
    """
    Load a table by name (table_name should be the sheet name or prepared table name).
    If table_name matches a sheet name, we convert it to internal table name.
    """
    table = table_name
    # allow passing original sheet name
    if not table.startswith("sheet_"):
        table = _prepare_table_name(table_name)
    conn = _connect()
    try:
        q = f"SELECT * FROM '{table}'"
        if limit:
            q += f" LIMIT {int(limit)}"
        df = pd.read_sql_query(q, conn)
        return df
    finally:
        conn.close()

def load_all() -> Dict[str, pd.DataFrame]:
    """
    Retourne toutes les tables importées (nom_table -> DataFrame)
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        res = {}
        for t in tables:
            res[t] = pd.read_sql_query(f"SELECT * FROM '{t}'", conn)
        return res
    finally:
        conn.close()

def ensure_db_exists():
    # simple helper to create DB file if missing
    if not DB_PATH.exists():
        conn = _connect()
        conn.close()
