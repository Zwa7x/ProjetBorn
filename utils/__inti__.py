# utils/__init__.py
"""
Package utils : point d'entrée pour les utilitaires de l'application.
Expose explicitement les fonctions utilisées par l'app Streamlit.
"""

# Import explicite des modules utiles
from .settings_loader import load_settings, save_settings

# Si vous avez un module utilitaire (anciennement utils.py), renommez-le en helpers.py
# et exposez ici la fonction load_data (voir utils/helpers.py ci-dessous).
try:
    from .helpers import load_data
except Exception:
    # fallback : si helpers absent, on laisse l'import échouer plus tard avec message clair
    load_data = None

__all__ = ["load_settings", "save_settings", "load_data"]
