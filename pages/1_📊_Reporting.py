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
# Utilitaires robustes pour noms de colonnes et conversion
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
# Chargement des données (votre utilitaire)
# -------------------------
try:
    df = load_data()
    if df is None:
        df = pd.DataFrame()
except Exception as e:
    st.error(f"Erreur lors du chargement des données via load_data(): {e}")
    df = pd.DataFrame()

# Nettoyage basique des colonnes
if not df.empty:
    df.columns = df.columns.str.strip()

# -------------------------
# Sidebar : filtres (conserve votre logique REGION / LIEUX)
# -------------------------
st.subheader("🔍 Filtres")
regions = []
if "REGION" in df.columns:
    regions = df["REGION"].dropna().unique().tolist()
region_filter = st.selectbox("Région", ["Toutes"] + list(regions)) if regions else st.selectbox("Région", ["Toutes"])

df_temp = df.copy()
if region_filter != "Toutes" and "REGION" in df_temp.columns:
    df_temp = df_temp[df_temp["REGION"] == region_filter]

lieux = []
if "LIEUX" in df_temp.columns:
    lieux = df_temp["LIEUX"].dropna().unique().tolist()
lieu_filter = st.selectbox("Lieu", ["Tous"] + list(lieux)) if lieux else st.selectbox("Lieu", ["Tous"])

df_filtered = df_temp.copy()
if lieu_filter != "Tous" and "LIEUX" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["LIEUX"] == lieu_filter]

st.divider()

# -------------------------
# Debug rétractable / bouton pro
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
# Détection et standardisation de la colonne prix
# -------------------------
price_col_original = None
if not df_filtered.empty:
    price_col_original = find_best_column(df_filtered.columns.tolist(), "Prix du KwH", cutoff=0.5)
    if not price_col_original:
        # fallback : chercher colonne contenant 'prix' et 'kwh'
        for c in df_filtered.columns:
            if "prix" in normalize_colname(c) and "kwh" in normalize_colname(c):
                price_col_original = c
                break

if price_col_original:
    # renommer pour homogénéité
    try:
        df_filtered = df_filtered.rename(columns={price_col_original: "Prix du KwH"})
        price_col = "Prix du KwH"
    except Exception:
        price_col = price_col_original
else:
    price_col = None

# -------------------------
# Calculs des indicateurs (sécurisés)
# -------------------------
# Coût total
cout_total = None
if "Cout" in df_filtered.columns:
    try:
        cout_total = clean_numeric_series(df_filtered["Cout"]).sum(min_count=1)
    except Exception:
        cout_total = None

# Prix moyen kWh global
prix_kwh_global = None
if price_col and price_col in df_filtered.columns:
    try:
        prix_kwh_global = clean_numeric_series(df_filtered[price_col]).mean()
    except Exception:
        prix_kwh_global = None

# Vitesse moyenne globale
vitesse_moyenne_global = None
if "Vitesse kw/min" in df_filtered.columns:
    try:
        vitesse_moyenne_global = pd.to_numeric(df_filtered["Vitesse kw/min"], errors='coerce').mean()
    except Exception:
        vitesse_moyenne_global = None

# Temps total
temps_total = None
if "TEMPS en min" in df_filtered.columns:
    try:
        temps_total = pd.to_numeric(df_filtered["TEMPS en min"], errors='coerce').sum(min_count=1)
    except Exception:
        temps_total = None

# -------------------------
# Fonction card (style CUPRA conservé)
# -------------------------
def card(label, value, accent=None):
    return f"""
    <div style='padding:14px; border-radius:10px; background-color:#1a1a1a; color:#e6e6e6;'>
        <div style='font-size:14px; opacity:0.8;'>{label}</div>
        <div style='font-size:22px; font-weight:600;'>{value}</div>
        {f"<div style='font-size:14px; color:#d47f2a;'>{accent}</div>" if accent else ""}
    </div>
    """

# -------------------------
# Affichage résumé global (cartes)
# -------------------------
st.subheader("📌 Résumé global")
colA, colB, colC, colD = st.columns(4)

colA.markdown(card("Coût total (€)", f"{cout_total:.2f}" if cout_total is not None else "N/A"), unsafe_allow_html=True)
colB.markdown(card("Prix moyen du kWh", f"{prix_kwh_global:.3f} €/kWh" if prix_kwh_global is not None else "N/A"), unsafe_allow_html=True)
colC.markdown(card("Vitesse moyenne", f"{vitesse_moyenne_global:.2f} kw/min" if vitesse_moyenne_global else "N/A"), unsafe_allow_html=True)
colD.markdown(card("Temps total", f"{temps_total:.1f} min" if temps_total else "N/A"), unsafe_allow_html=True)

st.divider()

# -------------------------
# Indicateurs clés (top stations, vitesse, sessions)
# -------------------------
st.subheader("📈 Indicateurs clés")

# Prix moyen par LIEUX
prix_kwh_moyen_all = pd.Series(dtype=float)
if price_col and price_col in df_filtered.columns and "LIEUX" in df_filtered.columns:
    try:
        prix_kwh_moyen_all = df_filtered.groupby("LIEUX")[price_col].apply(lambda s: clean_numeric_series(s).mean()).sort_values()
    except Exception:
        prix_kwh_moyen_all = pd.Series(dtype=float)

# Vitesse moyenne par LIEUX
vitesse_moyenne_all = None
if "Vitesse kw/min" in df_filtered.columns and "LIEUX" in df_filtered.columns:
    try:
        vitesse_moyenne_all = df_filtered.groupby("LIEUX")["Vitesse kw/min"].apply(lambda s: pd.to_numeric(s, errors='coerce').mean()).sort_values(ascending=False)
    except Exception:
        vitesse_moyenne_all = None

nb_sessions = len(df_filtered)

# Réutilisation de la fonction card (taille légèrement différente)
def card_small(label, value, accent=None):
    return f"""
    <div style='padding:14px; border-radius:10px; background-color:#1a1a1a; color:#e6e6e6;'>
        <div style='font-size:14px; opacity:0.8;'>{label}</div>
        <div style='font-size:20px; font-weight:600;'>{value}</div>
        {f"<div style='font-size:14px; color:#d47f2a;'>{accent}</div>" if accent else ""}
    </div>
    """

col1, col2, col3 = st.columns(3)

# Station la moins chère
if not prix_kwh_moyen_all.empty:
    station_cheap = prix_kwh_moyen_all.index[0]
    prix_cheap = prix_kwh_moyen_all.iloc[0]
    col1.markdown(card_small("Station la moins chère", station_cheap, f"{prix_cheap:.3f} €/kWh"), unsafe_allow_html=True)
else:
    col1.markdown(card_small("Station la moins chère", "N/A"), unsafe_allow_html=True)

# Station la plus rapide
if vitesse_moyenne_all is not None and not vitesse_moyenne_all.empty:
    station_fast = vitesse_moyenne_all.index[0]
    vitesse_fast = vitesse_moyenne_all.iloc[0]
    col2.markdown(card_small("Station la plus rapide", station_fast, f"{vitesse_fast:.2f} kw/min"), unsafe_allow_html=True)
else:
    col2.markdown(card_small("Station la plus rapide", "N/A"), unsafe_allow_html=True)

# Nombre de sessions
col3.markdown(card_small("Nombre de sessions", f"{nb_sessions}"), unsafe_allow_html=True)

st.divider()

# -------------------------
# Top 10 moins chères (bar horizontal)
# -------------------------
st.subheader("💚 Top 10 des stations les moins chères (€/kWh)")
if price_col and price_col in df_filtered.columns and "LIEUX" in df_filtered.columns:
    try:
        prix_kwh_moyen = (
            df_filtered.groupby("LIEUX")[price_col]
            .apply(lambda s: clean_numeric_series(s).mean())
            .sort_values()
            .head(10)
            .reset_index()
            .iloc[::-1]
        )
        if not prix_kwh_moyen.empty:
            fig_low = px.bar(
                prix_kwh_moyen,
                x=price_col,
                y="LIEUX",
                orientation="h",
                title="Top 10 des stations les moins chères (€/kWh)",
            )
            fig_low.update_traces(texttemplate='%{x:.3f}', textposition='outside')
            st.plotly_chart(fig_low, use_container_width=True)
        else:
            st.info("Pas assez de données pour le top 10 moins chères.")
    except Exception as e:
        st.error(f"Erreur génération top moins chères : {e}")
else:
    st.info("Colonne prix ou LIEUX manquante pour le top 10 moins chères.")

# -------------------------
# Top 10 plus chères
# -------------------------
st.subheader("❤️ Top 10 des stations les plus chères (€/kWh)")
if price_col and price_col in df_filtered.columns and "LIEUX" in df_filtered.columns:
    try:
        prix_kwh_moyen_high = (
            df_filtered.groupby("LIEUX")[price_col]
            .apply(lambda s: clean_numeric_series(s).mean())
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
            .iloc[::-1]
        )
        if not prix_kwh_moyen_high.empty:
            fig_high = px.bar(
                prix_kwh_moyen_high,
                x=price_col,
                y="LIEUX",
                orientation="h",
                title="Top 10 des stations les plus chères (€/kWh)",
            )
            fig_high.update_traces(texttemplate='%{x:.3f}', textposition='outside')
            st.plotly_chart(fig_high, use_container_width=True)
        else:
            st.info("Pas assez de données pour le top 10 plus chères.")
    except Exception as e:
        st.error(f"Erreur génération top plus chères : {e}")
else:
    st.info("Colonne prix ou LIEUX manquante pour le top 10 plus chères.")

st.divider()

# -------------------------
# Top 10 plus rapides
# -------------------------
st.subheader("⚡ Top 10 des stations les plus rapides (kw/min)")
if "Vitesse kw/min" in df_filtered.columns and "LIEUX" in df_filtered.columns:
    try:
        vitesse_moyenne_full = (
            df_filtered.groupby("LIEUX")["Vitesse kw/min"]
            .apply(lambda s: pd.to_numeric(s, errors='coerce').mean())
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
            .iloc[::-1]
        )
        if not vitesse_moyenne_full.empty:
            fig_fast = px.bar(
                vitesse_moyenne_full,
                x="Vitesse kw/min",
                y="LIEUX",
                orientation="h",
                title="Top 10 des stations les plus rapides (kw/min)",
            )
            fig_fast.update_traces(texttemplate='%{x:.2f}', textposition='outside')
            st.plotly_chart(fig_fast, use_container_width=True)
        else:
            st.info("Pas assez de données pour le top 10 des plus rapides.")
    except Exception as e:
        st.error(f"Erreur génération top rapides : {e}")
else:
    st.info("Colonne 'Vitesse kw/min' ou 'LIEUX' manquante pour le top 10 rapides.")

st.divider()

# -------------------------
# Donut : répartition sessions par station
# -------------------------
st.subheader("🧁 Répartition du nombre de sessions par station")
if "LIEUX" in df_filtered.columns:
    try:
        sessions = df_filtered["LIEUX"].value_counts()
        if len(sessions) > 0:
            fig_sessions = px.pie(
                names=sessions.index,
                values=sessions.values,
                hole=0.5,
                title="Répartition des sessions par station"
            )
            fig_sessions.update_traces(textinfo='value')
            st.plotly_chart(fig_sessions, use_container_width=True)
        else:
            st.info("Aucune session pour afficher la répartition.")
    except Exception as e:
        st.error(f"Erreur donut sessions : {e}")
else:
    st.info("Colonne LIEUX manquante pour la répartition des sessions.")

# -------------------------
# Donut : coût par région
# -------------------------
st.subheader("🧁 Répartition du coût total par région")
if "REGION" in df_filtered.columns and "Cout" in df_filtered.columns:
    try:
        cout_region = df_filtered.groupby("REGION")["Cout"].apply(lambda s: clean_numeric_series(s).sum(min_count=1))
        if not cout_region.empty:
            fig_region = px.pie(
                names=cout_region.index,
                values=cout_region.values,
                hole=0.5,
                title="Répartition du coût total par région"
            )
            fig_region.update_traces(textinfo='value')
            st.plotly_chart(fig_region, use_container_width=True)
        else:
            st.info("Pas de coûts par région à afficher.")
    except Exception as e:
        st.error(f"Erreur donut coût par région : {e}")
else:
    st.info("Colonnes REGION ou Cout manquantes pour la répartition du coût.")

# -------------------------
# Donut : temps par type de borne
# -------------------------
st.subheader("🧁 Répartition du temps passé par type de borne")
if "TYPE_BORNE" in df_filtered.columns and "TEMPS en min" in df_filtered.columns:
    try:
        temps_borne = df_filtered.groupby("TYPE_BORNE")["TEMPS en min"].apply(lambda s: pd.to_numeric(s, errors='coerce').sum(min_count=1))
        if not temps_borne.empty:
            fig_temps = px.pie(
                names=temps_borne.index,
                values=temps_borne.values,
                hole=0.5,
                title="Répartition du temps passé par type de borne"
            )
            fig_temps.update_traces(textinfo='label+value')
            st.plotly_chart(fig_temps, use_container_width=True)
        else:
            st.info("Pas de données temps par type de borne.")
    except Exception as e:
        st.error(f"Erreur donut temps par type de borne : {e}")
else:
    st.info("Colonnes TYPE_BORNE ou TEMPS en min manquantes pour ce graphique.")

st.divider()

# -------------------------
# Radar chart : comparatif entre deux stations
# -------------------------
st.subheader("🛡️ Comparatif entre deux stations")
stations = []
if "LIEUX" in df_filtered.columns:
    stations = df_filtered["LIEUX"].dropna().unique().tolist()

colA, colB = st.columns(2)
station_A = colA.selectbox("Station A", stations) if stations else colA.selectbox("Station A", ["N/A"])
station_B = colB.selectbox("Station B", stations) if stations else colB.selectbox("Station B", ["N/A"])

def stats_station(df_local, station):
    subset = df_local[df_local["LIEUX"] == station] if "LIEUX" in df_local.columns else pd.DataFrame()
    return {
        "Prix moyen du kWh": clean_numeric_series(subset["Prix du KwH"]).mean() if "Prix du KwH" in subset.columns else 0,
        "Vitesse moyenne (kw/min)": pd.to_numeric(subset["Vitesse kw/min"], errors='coerce').mean() if "Vitesse kw/min" in subset.columns else 0,
        "Sessions": len(subset),
        "Temps moyen (min)": pd.to_numeric(subset["TEMPS en min"], errors='coerce').mean() if "TEMPS en min" in subset.columns else 0
    }

stats_A = stats_station(df_filtered, station_A) if station_A != "N/A" else {k:0 for k in ["Prix moyen du kWh","Vitesse moyenne (kw/min)","Sessions","Temps moyen (min)"]}
stats_B = stats_station(df_filtered, station_B) if station_B != "N/A" else {k:0 for k in ["Prix moyen du kWh","Vitesse moyenne (kw/min)","Sessions","Temps moyen (min)"]}

categories = list(stats_A.keys())
fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(r=list(stats_A.values()), theta=categories, fill='toself', name=str(station_A)))
fig_radar.add_trace(go.Scatterpolar(r=list(stats_B.values()), theta=categories, fill='toself', name=str(station_B)))
fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), title="Comparatif des performances entre deux stations")
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# -------------------------
# Évolution mensuelle du coût
# -------------------------
st.subheader("📅 Évolution mensuelle du coût")
if "Date" in df_filtered.columns:
    try:
        df_filtered["Date"] = pd.to_datetime(df_filtered["Date"], errors="coerce")
        df_filtered = df_filtered.dropna(subset=["Date"])
        if len(df_filtered) > 0 and "Cout" in df_filtered.columns:
            df_filtered["Mois"] = df_filtered["Date"].dt.to_period("M").astype(str)
            df_mois = df_filtered.groupby("Mois")["Cout"].apply(lambda s: clean_numeric_series(s).sum(min_count=1)).reset_index()
            if not df_mois.empty:
                fig4 = px.line(df_mois, x="Mois", y="Cout", title="Coût total par mois (€)")
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Pas de données mensuelles de coût à afficher.")
        else:
            st.info("Données Date ou Cout insuffisantes pour l'évolution mensuelle.")
    except Exception as e:
        st.error(f"Erreur évolution mensuelle : {e}")
else:
    st.info("Colonne 'Date' absente : impossible de tracer l'évolution mensuelle.")

# -------------------------
# Footer conseils
# -------------------------
st.markdown("---")
st.markdown("**Conseils**")
st.markdown("- Activez le debug dans la sidebar pour voir les colonnes et aperçus si un graphique manque.")
st.markdown("- Si une colonne n'est pas détectée automatiquement (ex: Prix du KwH), vérifiez le nom exact dans le debug et adaptez vos données ou la logique de détection.")
