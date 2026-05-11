# backend/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from pathlib import Path
from typing import Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "settings.db"

app = FastAPI(title="Settings API")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class RegionIn(BaseModel):
    acronym: str
    long_name: Optional[str] = None

class PlaceIn(BaseModel):
    name: str
    region_acronym: str
    address: Optional[str] = None

class ChargerIn(BaseModel):
    code: str
    label: str
    specs: Optional[dict] = None

@app.get("/api/regions")
def list_regions():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM region_summary").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/regions", status_code=201)
def create_region(r: RegionIn):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO regions(acronym,long_name) VALUES(?,?)", (r.acronym, r.long_name or r.acronym))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    conn.close()
    return {"acronym": r.acronym, "long_name": r.long_name}

@app.put("/api/regions/{acronym}")
def update_region(acronym: str, r: RegionIn):
    conn = get_conn()
    cur = conn.execute("UPDATE regions SET long_name=? WHERE acronym=?", (r.long_name, acronym))
    conn.commit()
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Region not found")
    conn.close()
    return {"acronym": acronym, "long_name": r.long_name}

@app.delete("/api/regions/{acronym}")
def delete_region(acronym: str):
    conn = get_conn()
    # check places count
    cnt = conn.execute("SELECT COUNT(*) as c FROM places WHERE region_acronym=?", (acronym,)).fetchone()["c"]
    if cnt > 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Region has places attached")
    cur = conn.execute("DELETE FROM regions WHERE acronym=?", (acronym,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Region not found")
    return {"deleted": acronym}

# Places endpoints
@app.get("/api/places")
def list_places():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM places").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/places", status_code=201)
def create_place(p: PlaceIn):
    conn = get_conn()
    # validate region exists
    r = conn.execute("SELECT 1 FROM regions WHERE acronym=?", (p.region_acronym,)).fetchone()
    if not r:
        conn.close()
        raise HTTPException(status_code=400, detail="Region does not exist")
    cur = conn.execute("INSERT INTO places(name,region_acronym,address) VALUES(?,?,?)", (p.name, p.region_acronym, p.address))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return {"id": pid, "name": p.name}

@app.put("/api/places/{place_id}")
def update_place(place_id: int, p: PlaceIn):
    conn = get_conn()
    cur = conn.execute("UPDATE places SET name=?, region_acronym=?, address=? WHERE id=?", (p.name, p.region_acronym, p.address, place_id))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Place not found")
    return {"id": place_id}

@app.delete("/api/places/{place_id}")
def delete_place(place_id: int):
    conn = get_conn()
    cur = conn.execute("DELETE FROM places WHERE id=?", (place_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Place not found")
    return {"deleted": place_id}

# Charger types endpoints
@app.get("/api/chargers")
def list_chargers():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM charger_types").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/chargers", status_code=201)
def create_charger(c: ChargerIn):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO charger_types(code,label,specs) VALUES(?,?,?)", (c.code, c.label, json.dumps(c.specs or {})))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    conn.close()
    return {"code": c.code, "label": c.label}
