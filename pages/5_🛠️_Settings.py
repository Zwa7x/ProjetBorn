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
