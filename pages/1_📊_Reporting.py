# 1_📊_Reporting.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import unicodedata
import difflib
from utils import load_data

st.set_page_config(page_title="Reporting", layout="wide")

# --- MODE SOMBRE CUPRA (conserve votre style) ---
if "theme_cupra" in st.session_state and st.session_state.theme_cupra:
    st.markdown("""
    <style>
    body, .stApp { background-color: #0d0d0d; color: #e6e6e6; }
    h1, h2, h3, h4 { color: #d47f2a !important; }
    .js-plotly-plot .plotly .main-svg { background-color: #0d0d0d !important; }
    .stButton>button { background-color: #d47f2a; color: white; border-radius: 8px; border: none; }
    .stButton>button:hover { background-color: #b86c22; }
    .stSelectbox>div>div { background-color: #1a1a1a; color: #e6e6e6; }
    </style>
    """, unsafe_allow_html=True)

st.header("📊 Reporting")

# -------------------------
# Utilitaires robustes
# -------------------------
def normalize_colname(name: str) -> str:
    name = str(name).strip().lower()
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = " ".join(name.split())
    return name

def find_best_column(df_cols, target, cutoff=0.5):
    norm_cols = [normalize_colname(c) for c in df_cols]
    target_norm = normalize_colname(target)
    if target_norm in norm_cols:
        return df_cols[norm_cols.index(target_norm)]
    matches = difflib.get_close_matches(target_norm, norm_cols, n=3, cutoff=cutoff)
    if matches:
        return df_cols[norm_cols.index(matches[0])]
    return None

def clean_numeric_series(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.replace('\xa0', ' ', regex=False)
    s = s.str.replace('€', '', regex=False)
    s = s.str.replace(',', '.', regex=False)
    s = s.str.strip()
    return pd.to_numeric(s, errors='coerce')

# -------------------------
# Chargement des données
# -------------------------
try:
    df = load_data()
    if df is None:
        df = pd.DataFrame()
except Exception as e:
    st.error(f"Erreur lors du chargement des données via load_data(): {e}")
    df = pd.DataFrame()

if not df.empty:
    df.columns = df.columns.str.strip()

# -------------------------
# Sidebar : filtres (REGION / LIEUX / Dates / options)
# -------------------------
st.sidebar.header("Filtres")

# Région / Lieux (votre logique existante)
regions = df["REGION"].dropna().unique().tolist() if "REGION" in df.columns else []
region_filter = st.sidebar.selectbox("Région", ["Toutes"] + list(regions)) if regions else st.sidebar.selectbox("Région", ["Toutes"])

df_temp = df.copy()
if region_filter != "Toutes" and "REGION" in df_temp.columns:
    df_temp = df_temp[df_temp["REGION"] == region_filter]

lieux = df_temp["LIEUX"].dropna().unique().tolist() if "LIEUX" in df_temp.columns else []
lieu_filter = st.sidebar.selectbox("Lieu", ["Tous"] + list(lieux)) if lieux else st.sidebar.selectbox("Lieu", ["Tous"])

# --- Filtre date avancé ---
# Détection colonne date possible
date_col_candidates = [c for c in df.columns if normalize_colname(c) in ("date", "dateheure", "timestamp")]
date_col = date_col_candidates[0] if date_col_candidates else ( "Date" if "Date" in df.columns else None )

st.sidebar.markdown("### Période")
period_mode = st.sidebar.radio("Mode période", ("Période personnalisée", "Année glissante (12 mois)", "Année entière"), index=0)

# Si année entière, proposer choix d'année
available_years = []
if date_col and date_col in df.columns:
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        available_years = sorted(df[date_col].dropna().dt.year.unique().tolist())
    except Exception:
        available_years = []

# Widgets selon mode
if period_mode == "Période personnalisée":
    date_range = st.sidebar.date_input("Sélectionner période", value=(df[date_col].min() if date_col and not df[date_col].isna().all() else None, df[date_col].max() if date_col and not df[date_col].isna().all() else None))
elif period_mode == "Année glissante (12 mois)":
    # calculer fin = max date disponible, début = fin - 12 mois
    if date_col and not df[date_col].isna().all():
        max_date = df[date_col].max()
        min_date = max_date - pd.DateOffset(months=12)
        date_range = (min_date.date(), max_date.date())
        st.sidebar.write(f"Année glissante : {date_range[0]} → {date_range[1]}")
    else:
        date_range = None
else:  # Année entière
    year_choice = st.sidebar.selectbox("Année", ["Toutes"] + [str(y) for y in available_years]) if available_years else st.sidebar.selectbox("Année", ["Toutes"])
    if year_choice and year_choice != "Toutes" and date_col:
        y = int(year_choice)
        date_range = (pd.Timestamp(year=y, month=1, day=1).date(), pd.Timestamp(year=y, month=12, day=31).date())
    else:
        date_range = None

# Option regroupement "Autres" pour pie sessions
st.sidebar.markdown("### Options graphiques")
group_method = st.sidebar.selectbox("Regrouper petites stations", ("Regrouper celles à 1 session", "Top N stations (autres → Autres)"), index=0)
top_n = st.sidebar.slider("Top N (si sélection Top N)", min_value=5, max_value=50, value=10, step=1)

# Appliquer filtres Région / LIEUX
df_filtered = df_temp.copy()
if lieu_filter != "Tous" and "LIEUX" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["LIEUX"] == lieu_filter]

# Appliquer filtre date si défini
if date_range and date_col and date_col in df_filtered.columns and date_range[0] is not None:
    try:
        start, end = date_range
        df_filtered = df_filtered[(df_filtered[date_col] >= pd.to_datetime(start)) & (df_filtered[date_col] <= pd.to_datetime(end))]
    except Exception:
        pass

st.divider()

# -------------------------
# Debug rétractable
# -------------------------
show_debug_sidebar = st.sidebar.checkbox("Afficher debug", value=False)
with st.expander("🔧 Debug colonnes et aperçu", expanded=show_debug_sidebar):
    try:
        st.write("Nombre de lignes :", len(df_filtered))
        st.write("Colonnes disponibles :", df_filtered.columns.tolist())
        st.write("Aperçu des 5 premières lignes :", df_filtered.head())
    except Exception as e:
        st.error(f"Impossible d'afficher df_filtered: {e}")

# -------------------------
# Détection colonne prix et standardisation
# -------------------------
price_col_original = None
if not df_filtered.empty:
    price_col_original = find_best_column(df_filtered.columns.tolist(), "Prix du KwH", cutoff=0.5)
    if not price_col_original:
        for c in df_filtered.columns:
            if "prix" in normalize_colname(c) and "kwh" in normalize_colname(c):
                price_col_original = c
                break

if price_col_original:
    try:
        df_filtered = df_filtered.rename(columns={price_col_original: "Prix du KwH"})
        price_col = "Prix du KwH"
    except Exception:
        price_col = price_col_original
else:
    price_col = None

# -------------------------
# Calculs indicateurs
# -------------------------
cout_total = None
if "Cout" in df_filtered.columns:
    cout_total = clean_numeric_series(df_filtered["Cout"]).sum(min_count=1)

prix_kwh_global = None
if price_col and price_col in df_filtered.columns:
    prix_kwh_global = clean_numeric_series(df_filtered[price_col]).mean()

vitesse_moyenne_global = None
if "Vitesse kw/min" in df_filtered.columns:
    vitesse_moyenne_global = pd.to_numeric(df_filtered["Vitesse kw/min"], errors='coerce').mean()

temps_total = None
if "TEMPS en min" in df_filtered.columns:
    temps_total = pd.to_numeric(df_filtered["TEMPS en min"], errors='coerce').sum(min_count=1)

# -------------------------
# Cartes résumé
# -------------------------
def card(label, value, accent=None):
    return f"""
    <div style='padding:14px; border-radius:10px; background-color:#1a1a1a; color:#e6e6e6;'>
        <div style='font-size:14px; opacity:0.8;'>{label}</div>
        <div style='font-size:22px; font-weight:600;'>{value}</div>
        {f"<div style='font-size:14px; color:#d47f2a;'>{accent}</div>" if accent else ""}
    </div>
    """

st.subheader("📌 Résumé global")
colA, colB, colC, colD = st.columns(4)
colA.markdown(card("Coût total (€)", f"{cout_total:.2f}" if cout_total is not None else "N/A"), unsafe_allow_html=True)
colB.markdown(card("Prix moyen du kWh", f"{prix_kwh_global:.3f} €/kWh" if prix_kwh_global is not None else "N/A"), unsafe_allow_html=True)
colC.markdown(card("Vitesse moyenne", f"{vitesse_moyenne_global:.2f} kw/min" if vitesse_moyenne_global else "N/A"), unsafe_allow_html=True)
colD.markdown(card("Temps total", f"{temps_total:.1f} min" if temps_total else "N/A"), unsafe_allow_html=True)

st.divider()

# -------------------------
# Indicateurs clés
# -------------------------
st.subheader("📈 Indicateurs clés")
prix_kwh_moyen_all = pd.Series(dtype=float)
if price_col and price_col in df_filtered.columns and "LIEUX" in df_filtered.columns:
    prix_kwh_moyen_all = df_filtered.groupby("LIEUX")[price_col].apply(lambda s: clean_numeric_series(s
