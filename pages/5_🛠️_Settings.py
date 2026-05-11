# --- quick restore session_state from DB (paste at top, after import streamlit as st) ---
try:
    # reload settings from DB and rehydrate session state
    _settings_tmp = load_settings()
    if isinstance(_settings_tmp, dict):
        st.session_state["settings_from_db"] = _settings_tmp
        # rebuild regions_df used by la page
        def _settings_to_regions_df(s):
            import pandas as _pd
            rows = []
            for name, meta in (s.get("regions") or {}).items():
                acr = meta.get("acronyme", "") if isinstance(meta, dict) else ""
                lieux = meta.get("lieux", []) if isinstance(meta, dict) else []
                rows.append({"Supprimer": False, "Région": name, "Acronyme": acr, "Lieux (séparés par ,)": ", ".join(lieux)})
            if not rows:
                return _pd.DataFrame(columns=["Supprimer", "Région", "Acronyme", "Lieux (séparés par ,)"])
            return _pd.DataFrame(rows)
        st.session_state["regions_df"] = _settings_to_regions_df(_settings_tmp)
        st.session_state["settings_loaded_ok"] = True
        st.experimental_rerun()
except Exception as _e:
    st.error("Restore session_state failed: " + str(_e))


import streamlit as st
import pandas as pd
import traceback
from utils import load_settings, save_settings

# Petit CSS pour ajustements visuels (placer juste après l'import de streamlit)
st.markdown(
    """
    <style>
    /* réduire la largeur de la première colonne (case Supprimer) */
    div[data-testid="stDataFrameContainer"] table th:first-child,
    div[data-testid="stDataFrameContainer"] table td:first-child,
    .stDataFrame table th:first-child,
    .stDataFrame table td:first-child {
        width: 48px !important;
        max-width: 48px !important;
        text-align: center;
        padding-left: 6px !important;
        padding-right: 6px !important;
    }
    /* titre d'édition plus discret */
    .small-edit-title { font-size: 0.95rem; margin-bottom: 0.25rem; color: #111827; }
    /* menu contextuel horizontal et compact */
    .top-right-menu { display:flex; justify-content:flex-end; gap:8px; align-items:center; }
    .top-right-menu button { margin:0 2px; }
    </style>
    """,
    unsafe_allow_html=True,
)
