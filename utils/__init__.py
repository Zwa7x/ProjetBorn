# utils/__init__.py
# Expose les fonctions publiques du package utils

# Importer explicitement les fonctions depuis leurs modules respectifs.
# Ajuste les noms de modules si tu utilises d'autres fichiers (ex: data_loader.py).
try:
    from .settings_loader import load_settings, save_settings
except Exception:
    # fallback silencieux pour debug ; l'erreur sera visible si on tente d'utiliser la fonction
    load_settings = None
    save_settings = None

try:
    from .data_loader import load_data, save_data
except Exception:
    load_data = None
    save_data = None

__all__ = [
    "load_settings",
    "save_settings",
    "load_data",
    "save_data",
]
