# DEBUG DIAGNOSTIC — coller en tout début de pages/5_🛠️_Settings.py
import streamlit as st, traceback, ast, pathlib, sys, importlib
from pathlib import Path

st.set_page_config(page_title="DEBUG DIAGNOSTIC", layout="wide")
st.title("DEBUG DIAGNOSTIC — Vérification import / DB / settings")

p = Path(__file__).resolve()
st.write("Fichier page :", str(p))
# 1) Vérifier la syntaxe du fichier page
try:
    code = p.read_text(encoding="utf-8")
    try:
        ast.parse(code, filename=str(p))
        st.success("AST parse OK pour la page")
    except SyntaxError as se:
        st.error(f"SyntaxError dans la page: {se.msg} (ligne {se.lineno}, col {se.offset})")
        st.code(se.text or "", language="python")
        lines = code.splitlines()
        start = max(0, (se.lineno or 1) - 4)
        end = min(len(lines), (se.lineno or 1) + 2)
        excerpt = "\n".join(f"{i+1:4d}: {lines[i]}" for i in range(start, end))
        st.code(excerpt, language="python")
        st.stop()
except Exception as e:
    st.error("Impossible de lire/parse la page: " + str(e))
    st.text(traceback.format_exc())
    st.stop()

# 2) Tester l'import de utils et du loader
st.markdown("**Import utils / settings_loader**")
try:
    import utils
    st.success("Module utils importé")
except Exception as e:
    st.error("Erreur import utils: " + str(e))
    st.text(traceback.format_exc())
    st.stop()

try:
    # forcer le rechargement pour éviter cache stale
    import importlib
    importlib.reload(utils)
    from utils import load_settings, save_settings
    st.success("load_settings et save_settings importés depuis utils")
except Exception as e:
    st.error("Erreur import load_settings/save_settings: " + str(e))
    st.text(traceback.format_exc())
    # tenter import direct du module
    try:
        import utils.settings_loader as sl
        importlib.reload(sl)
        st.write("Import direct utils.settings_loader OK")
    except Exception as e2:
        st.error("Erreur import direct utils.settings_loader: " + str(e2))
        st.text(traceback.format_exc())
    st.stop()

# 3) Vérifier existence et permissions du fichier DB / JSON
ROOT = Path(__file__).resolve().parent.parent
data_dir = ROOT / "data"
db_path = data_dir / "settings.db"
json_path = data_dir / "settings.json"

st.write("Data dir:", str(data_dir))
st.write("DB path:", str(db_path), "exists:", db_path.exists())
if db_path.exists():
    try:
        st.write("DB size (bytes):", db_path.stat().st_size)
    except Exception as e:
        st.write("Impossible de lire la taille du DB:", e)

st.write("JSON path:", str(json_path), "exists:", json_path.exists())
if json_path.exists():
    try:
        st.write("JSON size (bytes):", json_path.stat().st_size)
    except Exception as e:
        st.write("Impossible de lire la taille du JSON:", e)

# 4) Si DB existe, lister les tables (sécurisé)
if db_path.exists():
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        st.write("Tables dans DB:", tables)
        conn.close()
    except Exception as e:
        st.write("Erreur lecture schema DB:", e)
        st.text(traceback.format_exc())

# 5) Appeler load_settings() et afficher résumé
st.markdown("**Appel load_settings()**")
try:
    s = load_settings()
    st.success("load_settings() exécuté")
    st.write("Type retourné:", type(s).__name__)
    if isinstance(s, dict):
        st.write("Clés racine:", list(s.keys()))
        st.write("Nombre de régions:", len(s.get("regions", {})))
        st.write("Types de borne (ex.):", (s.get("types_borne")[:5] if isinstance(s.get("types_borne"), list) else s.get("types_borne")))
    else:
        st.warning("load_settings() ne renvoie pas un dict")
except Exception as e:
    st.error("load_settings() a levé une exception: " + str(e))
    st.text(traceback.format_exc())
    st.stop()

st.info("DEBUG DIAGNOSTIC terminé — copie ici tout ce qui s'affiche.")
# Fin DEBUG DIAGNOSTIC


# utils/settings_loader.py
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
    # create DB file if missing; connect normally
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def _init_schema_if_missing():
    """
    Create the minimal schema if tables do not exist.
    Safe to call repeatedly.
    """
    _ensure_data_dir()
    # If DB file doesn't exist, connecting will create it; ensure tables exist
    conn = _get_conn()
    try:
        conn.executescript("""
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
        """)
    finally:
        conn.close()

def load_settings() -> Dict[str, Any]:
    """
    Retourne {"regions": {...}, "types_borne": [...]}
    - regions: clé = long_name (ou acronym si pas de long_name), valeur = {"acronyme":..., "lieux":[...]}
    - types_borne: liste d'objets {"code","label","specs"} (ou liste de strings si tu préfères)
    """
    _init_schema_if_missing()
    conn = _get_conn()
    cur = conn.cursor()

    # regions
    cur.execute("SELECT acronym, long_name FROM regions")
    regs = {}
    for row in cur.fetchall():
        long_name = row["long_name"] or row["acronym"]
        regs[long_name] = {"acronyme": row["acronym"], "lieux": []}

    # places -> attach to regions by acronym (try to find matching long_name)
    cur.execute("SELECT name, region_acronym FROM places")
    for row in cur.fetchall():
        ra = row["region_acronym"]
        # find region key by matching acronym
        found = None
        for k, v in regs.items():
            if v.get("acronyme") == ra:
                found = k
                break
        if not found:
            # fallback: use acronym as key
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
    """
    Écrase le contenu de la DB à partir du dict settings.
    Utilise une transaction pour garantir l'atomicité.
    """
    _init_schema_if_missing()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        # clear tables
        cur.execute("DELETE FROM places")
        cur.execute("DELETE FROM regions")
        cur.execute("DELETE FROM charger_types")

        # insert regions and places
        for region_key, meta in (settings.get("regions") or {}).items():
            # meta peut être dict ou autre ; normaliser
            if isinstance(meta, dict):
                acr = meta.get("acronyme") or region_key
                lieux = meta.get("lieux") or []
            else:
                acr = str(meta) if meta else region_key
                lieux = []
            long_name = region_key
            cur.execute(
                "INSERT INTO regions(acronym,long_name) VALUES(?,?)",
                (acr, long_name)
            )
            for lieu in (lieux or []):
                cur.execute(
                    "INSERT INTO places(name,region_acronym,address) VALUES(?,?,?)",
                    (str(lieu), acr, "")
                )

        # insert charger types
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
                # ignore unknown formats
                continue
            cur.execute(
                "INSERT INTO charger_types(code,label,specs) VALUES(?,?,?)",
                (code, label, json.dumps(specs))
            )

        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        raise
    finally:
        conn.close()
