# utils/__init__.py
# Minimal safe exports to avoid import-time failures.
# This file intentionally imports only settings_loader at module import time.

from .settings_loader import load_settings, save_settings

__all__ = ["load_settings", "save_settings"]
