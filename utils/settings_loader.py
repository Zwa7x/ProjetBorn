import json
import os

SETTINGS_PATH = os.path.join("data", "settings.json")

def load_settings():
    """Charge les paramètres depuis settings.json."""
    if not os.path.exists(SETTINGS_PATH):
        return {"regions": {}, "types_borne": []}

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(settings: dict):
    """Sauvegarde les paramètres dans settings.json."""
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
