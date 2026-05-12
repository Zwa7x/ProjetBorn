# utils/data_loader.py
import sqlite3
from pathlib import Path
import pandas as pd
import hashlib, json
from typing import Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "app_data.db"

def _connect():
    return sqlite3.connect(str(DB_PATH), timeout=30)

def _row_hash(row: pd.Series) -> str:
    s = json.dumps(row.fillna("").to_dict(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def _prepare_table_name(sheet_name: str) -> str:
    return "sheet_" + "".join(c if c.isalnum() else "_" for c in sheet_name).lower()

def ingest_excel(excel_path: str, mapping: Optional[Dict[str, Dict[str, str]]] = None, sheets: Optional[list] = None, mode: str = "upsert"):
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"{excel_path} not found")
    xls = pd.read_excel(excel_path, sheet_name=None, dtype=str)
    to_process = sheets or list(xls.keys())
    conn = _connect()
    try:
        for sheet in to_process:
            if sheet not in xls:
                continue
            df = xls[sheet].copy()
            if mapping and sheet in mapping:
                df = df.rename(columns=mapping[sheet])
            df.columns = [str(c).strip() for c in df.columns]
            df.columns = ["".join(ch if ch.isalnum() or ch=='_' else '_' for ch in str(c)).lower() for c in df.columns]
            table = _prepare_table_name(sheet)
            df["_row_hash"] = df.apply(_row_hash, axis=1)
            cur = conn.cursor()
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
            if mode == "replace":
                df.to_sql(table, conn, if_exists="append", index=False)
            else:
                cur.execute(f'SELECT _row_hash FROM "{table}"')
                existing_hashes = set(r[0] for r in cur.fetchall())
                new_rows = df[~df["_row_hash"].isin(existing_hashes)].copy()
                if not new_rows.empty:
                    new_rows.to_sql(table, conn, if_exists="append", index=False)
            conn.commit()
    finally:
        conn.close()

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

def load_all() -> Dict[str, pd.DataFrame]:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        res = {}
        for t in tables:
            res[t] = pd.read_sql_query(f'SELECT * FROM "{t}"', conn)
        return res
    finally:
        conn.close()

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
