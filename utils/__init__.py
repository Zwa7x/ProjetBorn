# utils/__init__.py
"""
Exports publics du package utils.
Les fonctions data sont importées à la demande pour éviter les import-circulaires.
"""

import importlib
from typing import Any

__all__ = ["load_settings", "save_settings", "load_data", "save_data"]

def load_settings(*args, **kwargs) -> Any:
    mod = importlib.import_module(".settings_loader", __package__)
    return getattr(mod, "load_settings")(*args, **kwargs)

def save_settings(*args, **kwargs) -> Any:
    mod = importlib.import_module(".settings_loader", __package__)
    return getattr(mod, "save_settings")(*args, **kwargs)

def load_data(*a, **k):
    mod = importlib.import_module(".data_loader", __package__)
    # exemple : renvoyer la table principale "mesures" si elle existe
    try:
        return mod.load_table("mesures")
    except Exception:
        # fallback : renvoyer toutes les tables
        return mod.load_all()

def save_data(*args, **kwargs) -> Any:
    mod = importlib.import_module(".data_loader", __package__)
    return getattr(mod, "save_data")(*args, **kwargs)

