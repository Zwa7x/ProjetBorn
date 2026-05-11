import json
import os

if not DB_PATH.exists():
    from scripts.init_db import init_db
    init_db()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SETTINGS_PATH = os.path.join(ROOT_DIR, "data", "settings.json")

DEFAULT_SETTINGS = {
    "regions": {},
    "types_borne": []
}

def _ensure_data_dir():
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)

def load_settings():
    _ensure_data_dir()

    if not os.path.exists(SETTINGS_PATH):
        return DEFAULT_SETTINGS.copy()

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        settings = json.load(f)

    settings.setdefault("regions", {})
    settings.setdefault("types_borne", [])

    return settings

def save_settings(settings: dict):
    _ensure_data_dir()
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
