# 1_📊_Reporting.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import unicodedata
import difflib
from utils import load_data, save_data
import traceback

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

def safe_min_max_dates(series):
    try:
        s = pd.to_datetime(series, errors='coerce')
        if s.dropna().empty:
            return None, None
        return s.min().date(), s.max().date()
    except Exception:
        return None, None

# -------------------------
# Chargement des données
# -------------------------
try:
    df = load_data()
    if df is None:
        df = pd.DataFrame()
except Exception:
    st.error("Erreur lors du chargement des données via load_data(). Voir le détail ci‑dessous.")
    st.text(traceback.format_exc())
    df = pd.DataFrame()

if not df.empty:
    df.columns = df.columns.str.strip()

# Détecter et convertir colonne date si présente (précoce)
date_col_candidates = [c for c in df.columns if normalize_colname(c) in ("date", "dateheure", "timestamp")]
date_col_detected = date_col_candidates[0] if date_col_candidates else ("Date" if "Date" in df.columns else None)
if date_col_detected and date_col_detected in df.columns:
    try:
        df[date_col_detected] = pd.to_datetime(df[date_col_detected], errors='coerce')
    except Exception:
        pass

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
date_col = date_col_detected

st.sidebar.markdown("### Période")
period_mode = st.sidebar.radio("Mode période", ("Période personnalisée", "Année glissante (12 mois)", "Année entière"), index=0)

min_date, max_date = (None, None)
if date_col and date_col in df.columns:
    min_date, max_date = safe_min_max_dates(df[date_col])

date_range = None
if period_mode == "Période personnalisée":
    default_start = min_date if min_date is not None else pd.Timestamp.now().date()
    default_end = max_date if max_date is not None else pd.Timestamp.now().date()
    try:
        picked = st.sidebar.date_input("Sélectionner période", value=(default_start, default_end))
        if isinstance(picked, tuple) and len(picked) == 2:
            date_range = (picked[0], picked[1])
        else:
            date_range = (picked, picked) if picked is not None else None
    except Exception:
        date_range = None
elif period_mode == "Année glissante (12 mois)":
    if date_col and min_date is not None and max_date is not None:
        try:
            max_dt = pd.to_datetime(max_date)
            min_dt = max_dt - pd.DateOffset(months=12)
            date_range = (min_dt.date(), max_dt.date())
            st.sidebar.write(f"Année glissante : {date_range[0]} → {date_range[1]}")
        except Exception:
            date_range = None
    else:
        date_range = None
else:  # Année entière
    available_years = []
    if date_col and date_col in df.columns:
        try:
            available_years = sorted(df[date_col].dropna().dt.year.unique().tolist())
        except Exception:
            available_years = []
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

st.divider()

# Appliquer filtres Région / LIEUX
df_filtered = df_temp.copy()
if lieu_filter != "Tous" and "LIEUX" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["LIEUX"] == lieu_filter]

# Appliquer filtre date si défini
if date_range and date_col and date_col in df_filtered.columns and isinstance(date_range, (tuple, list)) and date_range[0] is not None:
    try:
        start, end = date_range
        df_filtered = df_filtered[(pd.to_datetime(df_filtered[date_col], errors='coerce') >= pd.to_datetime(start)) & (pd.to_datetime(df_filtered[date_col], errors='coerce') <= pd.to_datetime(end))]
    except Exception:
        st.sidebar.warning("Le filtre date n'a pas pu être appliqué (format de date inattendu). Voir debug pour plus d'infos.")

# -------------------------
# Debug rétractable
# -------------------------
show_debug_sidebar = st.sidebar.checkbox("Afficher debug", value=False)
with st.expander("🔧 Debug colonnes et aperçu", expanded=show_debug_sidebar):
    try:
        st.write("Nombre de lignes :", len(df_filtered))
        st.write("Colonnes disponibles :", df_filtered.columns.tolist())
        st.write("Aperçu des 5 premières lignes :", df_filtered.head())
        st.write("Types de colonnes :")
        st.write(df_filtered.dtypes)
    except Exception:
        st.error("Impossible d'afficher df_filtered:")
        st.text(traceback.format_exc())

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
# Calculs indicateurs (sécurisés)
# -------------------------
try:
    cout_total = clean_numeric_series(df_filtered["Cout"]).sum(min_count=1) if "Cout" in df_filtered.columns else None
except Exception:
    cout_total = None

try:
    prix_kwh_global = clean_numeric_series(df_filtered[price_col]).mean() if price_col and price_col in df_filtered.columns else None
except Exception:
    prix_kwh_global = None

try:
    vitesse_moyenne_global = pd.to_numeric(df_filtered["Vitesse kw/min"], errors='coerce').mean() if "Vitesse kw/min" in df_filtered.columns else None
except Exception:
    vitesse_moyenne_global = None

try:
    temps_total = pd.to_numeric(df_filtered["TEMPS en min"], errors='coerce').sum(min_count=1) if "TEMPS en min" in df_filtered.columns else None
except Exception:
    temps_total = None

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
    try:
        prix_kwh_moyen_all = df_filtered.groupby("LIEUX")[price_col].apply(lambda s: clean_numeric_series(s).mean()).sort_values()
    except Exception:
        prix_kwh_moyen_all = pd.Series(dtype=float)

vitesse_moyenne_all = None
if "Vitesse kw/min" in df_filtered.columns and "LIEUX" in df_filtered.columns:
    try:
        vitesse_moyenne_all = df_filtered.groupby("LIEUX")["Vitesse kw/min"].apply(lambda s: pd.to_numeric(s, errors='coerce').mean()).sort_values(ascending=False)
    except Exception:
        vitesse_moyenne_all = None

nb_sessions = len(df_filtered)

def card_small(label, value, accent=None):
    return f"""
    <div style='padding:14px; border-radius:10px; background-color:#1a1a1a; color:#e6e6e6;'>
        <div style='font-size:14px; opacity:0.8;'>{label}</div>
        <div style='font-size:20px; font-weight:600;'>{value}</div>
        {f"<div style='font-size:14px; color:#d47f2a;'>{accent}</div>" if accent else ""}
    </div>
    """

col1, col2, col3 = st.columns(3)
if not prix_kwh_moyen_all.empty:
    station_cheap = prix_kwh_moyen_all.index[0]
    prix_cheap = prix_kwh_moyen_all.iloc[0]
    col1.markdown(card_small("Station la moins chère", station_cheap, f"{prix_cheap:.3f} €/kWh"), unsafe_allow_html=True)
else:
    col1.markdown(card_small("Station la moins chère", "N/A"), unsafe_allow_html=True)

if vitesse_moyenne_all is not None and not vitesse_moyenne_all.empty:
    station_fast = vitesse_moyenne_all.index[0]
    vitesse_fast = vitesse_moyenne_all.iloc[0]
    col2.markdown(card_small("Station la plus rapide", station_fast, f"{vitesse_fast:.2f} kw/min"), unsafe_allow_html=True)
else:
    col2.markdown(card_small("Station la plus rapide", "N/A"), unsafe_allow_html=True)

col3.markdown(card_small("Nombre de sessions", f"{nb_sessions}"), unsafe_allow_html=True)

st.divider()

# -------------------------
# Top N moins chères / plus chères / plus rapides (utilise top_n)
# -------------------------
st.subheader(f"💚 Top {top_n} des stations les moins chères (€/kWh)")
if price_col and price_col in df_filtered.columns and "LIEUX" in df_filtered.columns:
    try:
        prix_kwh_moyen = (
            df_filtered.groupby("LIEUX")[price_col]
            .apply(lambda s: clean_numeric_series(s).mean())
            .sort_values()
            .head(top_n)
            .reset_index()
            .iloc[::-1]
        )
        if not prix_kwh_moyen.empty:
            fig_low = px.bar(prix_kwh_moyen, x=price_col, y="LIEUX", orientation="h", title=f"Top {top_n} des stations les moins chères (€/kWh)")
            fig_low.update_traces(texttemplate='%{x:.3f}', textposition='outside')
            st.plotly_chart(fig_low, use_container_width=True)
        else:
            st.info("Pas assez de données pour le top moins chères.")
    except Exception:
        st.error("Erreur génération top moins chères :")
        st.text(traceback.format_exc())
else:
    st.info("Colonne prix ou LIEUX manquante pour le top moins chères.")

st.subheader(f"❤️ Top {top_n} des stations les plus chères (€/kWh)")
if price_col and price_col in df_filtered.columns and "LIEUX" in df_filtered.columns:
    try:
        prix_kwh_moyen_high = (
            df_filtered.groupby("LIEUX")[price_col]
            .apply(lambda s: clean_numeric_series(s).mean())
            .sort_values(ascending=False)
            .head(top_n)
            .reset_index()
            .iloc[::-1]
        )
        if not prix_kwh_moyen_high.empty:
            fig_high = px.bar(prix_kwh_moyen_high, x=price_col, y="LIEUX", orientation="h", title=f"Top {top_n} des stations les plus chères (€/kWh)")
            fig_high.update_traces(texttemplate='%{x:.3f}', textposition='outside')
            st.plotly_chart(fig_high, use_container_width=True)
        else:
            st.info("Pas assez de données pour le top plus chères.")
    except Exception:
        st.error("Erreur génération top plus chères :")
        st.text(traceback.format_exc())
else:
    st.info("Colonne prix ou LIEUX manquante pour le top plus chères.")

st.divider()

st.subheader(f"⚡ Top {top_n} des stations les plus rapides (kw/min)")
if "Vitesse kw/min" in df_filtered.columns and "LIEUX" in df_filtered.columns:
    try:
        vitesse_moyenne_full = (
            df_filtered.groupby("LIEUX")["Vitesse kw/min"]
            .apply(lambda s: pd.to_numeric(s, errors='coerce').mean())
            .sort_values(ascending=False)
            .head(top_n)
            .reset_index()
            .iloc[::-1]
        )
        if not vitesse_moyenne_full.empty:
            fig_fast = px.bar(vitesse_moyenne_full, x="Vitesse kw/min", y="LIEUX", orientation="h", title=f"Top {top_n} des stations les plus rapides (kw/min)")
            fig_fast.update_traces(texttemplate='%{x:.2f}', textposition='outside')
            st.plotly_chart(fig_fast, use_container_width=True)
        else:
            st.info("Pas assez de données pour le top des plus rapides.")
    except Exception:
        st.error("Erreur génération top rapides :")
        st.text(traceback.format_exc())
else:
    st.info("Colonne 'Vitesse kw/min' ou 'LIEUX' manquante pour le top rapides.")

st.divider()

# -------------------------
# Donut : répartition du nombre de sessions par station (avec regroupement Autres)
# - L'expander affiche maintenant les stations regroupées (l'inverse du Top N)
# -------------------------
st.subheader("🧁 Répartition du nombre de sessions par station")
if "LIEUX" in df_filtered.columns:
    try:
        sessions = df_filtered["LIEUX"].value_counts()
        if not sessions.empty:
            sessions_df = sessions.reset_index()
            sessions_df.columns = ["LIEUX", "count"]

            # Déterminer main_df et others_df selon la méthode choisie
            if group_method == "Regrouper celles à 1 session":
                main_df = sessions_df[sessions_df["count"] != 1].copy()
                others_df = sessions_df[sessions_df["count"] == 1].copy()
            else:  # Top N
                main_df = sessions_df.head(top_n).copy()
                others_df = sessions_df.iloc[top_n:].copy()

            others_count = int(others_df["count"].sum()) if not others_df.empty else 0
            others_stations_count = len(others_df)

            # Construire pie_df (main + ligne Autres si nécessaire)
            if others_count > 0:
                others_row = pd.DataFrame([{"LIEUX": "Autres", "count": others_count}])
                pie_df = pd.concat([main_df, others_row], ignore_index=True)
            else:
                pie_df = main_df

            pie_df = pie_df.sort_values("count", ascending=False)

            # Badge indiquant combien sont regroupés en "Autres"
            if others_count > 0:
                st.markdown(f"**Stations regroupées en 'Autres' :** `{others_stations_count}` stations, total sessions `{others_count}`", unsafe_allow_html=True)

            # Pie chart
            fig_sessions = px.pie(pie_df, names="LIEUX", values="count", hole=0.5, title="Répartition des sessions par station")
            fig_sessions.update_traces(textinfo='percent+value', textposition='inside')
            st.plotly_chart(fig_sessions, use_container_width=True)

            # Expander : afficher la liste des stations regroupées (inverse du Top N)
            with st.expander(f"Voir les stations regroupées (Autres) — {others_stations_count} éléments"):
                if not others_df.empty:
                    # Afficher les stations regroupées avec leur count
                    st.dataframe(others_df.reset_index(drop=True))
                else:
                    st.info("Aucune station regroupée dans 'Autres' pour la configuration actuelle.")
        else:
            st.info("Aucune session pour afficher la répartition.")
    except Exception:
        st.error("Erreur donut sessions :")
        st.text(traceback.format_exc())
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
            fig_region = px.pie(names=cout_region.index, values=cout_region.values, hole=0.5, title="Répartition du coût total par région")
            fig_region.update_traces(textinfo='value')
            st.plotly_chart(fig_region, use_container_width=True)
        else:
            st.info("Pas de coûts par région à afficher.")
    except Exception:
        st.error("Erreur donut coût par région :")
        st.text(traceback.format_exc())
else:
    st.info("Colonnes REGION ou Cout manquantes pour la répartition du coût.")

st.divider()

# -------------------------
# Donut : temps par type de borne (avec fallback)
# -------------------------
st.subheader("🧁 Répartition du temps passé par type de borne")
type_candidates = [c for c in df_filtered.columns if normalize_colname(c) in ("type_borne", "type borne", "typeborne", "type_bornes", "type")]
type_col = type_candidates[0] if type_candidates else ("TYPE_BORNE" if "TYPE_BORNE" in df_filtered.columns else None)

if type_col and "TEMPS en min" in df_filtered.columns:
    try:
        temps_borne = df_filtered.groupby(type_col)["TEMPS en min"].apply(lambda s: pd.to_numeric(s, errors='coerce').sum(min_count=1))
        if not temps_borne.empty:
            pie_df = pd.DataFrame({"type": temps_borne.index, "value": temps_borne.values})
            pie_df = pie_df.sort_values("value", ascending=False)
            if len(pie_df) > 10:
                topn = 10
                main = pie_df.head(topn)
                others = pie_df.iloc[topn:]["value"].sum()
                main = pd.concat([main, pd.DataFrame([{"type": "Autres", "value": others}])], ignore_index=True)
                pie_df = main
            fig_temps = px.pie(pie_df, names="type", values="value", hole=0.5, title="Répartition du temps passé par type de borne")
            fig_temps.update_traces(textinfo='label+value')
            st.plotly_chart(fig_temps, use_container_width=True)
        else:
            st.info("Pas de données temps par type de borne.")
    except Exception:
        st.error("Erreur donut temps par type de borne :")
        st.text(traceback.format_exc())
else:
    st.warning("Colonnes TYPE_BORNE ou TEMPS en min manquantes ou insuffisantes pour ce graphique.")
    if "TEMPS en min" in df_filtered.columns and "LIEUX" in df_filtered.columns:
        st.info("Affichage fallback : répartition du temps total par station (proxy si TYPE_BORNE absent).")
        try:
            temps_lieux = df_filtered.groupby("LIEUX")["TEMPS en min"].apply(lambda s: pd.to_numeric(s, errors='coerce').sum(min_count=1))
            if not temps_lieux.empty:
                temps_lieux = temps_lieux.sort_values(ascending=False)
                topn = min(10, len(temps_lieux))
                main = temps_lieux.head(topn)
                others = temps_lieux.iloc[topn:].sum() if len(temps_lieux) > topn else 0
                pie_df = pd.DataFrame({"LIEUX": main.index, "value": main.values})
                if others > 0:
                    pie_df = pd.concat([pie_df, pd.DataFrame([{"LIEUX": "Autres", "value": others}])], ignore_index=True)
                fig_temps_fallback = px.pie(pie_df, names="LIEUX", values="value", hole=0.5, title="Temps total par station (fallback)")
                fig_temps_fallback.update_traces(textinfo='label+value')
                st.plotly_chart(fig_temps_fallback, use_container_width=True)
            else:
                st.info("Pas de données TEMPS en min valides pour le fallback.")
        except Exception:
            st.error("Erreur fallback temps par station :")
            st.text(traceback.format_exc())
    else:
        st.info("Si vous souhaitez ce graphique, ajoutez une colonne 'TYPE_BORNE' et 'TEMPS en min' ou fournissez une colonne équivalente.")

st.divider()

# -------------------------
# Radar chart : comparatif entre deux stations
# -------------------------
st.subheader("🛡️ Comparatif entre deux stations")
stations = df_filtered["LIEUX"].dropna().unique().tolist() if "LIEUX" in df_filtered.columns else []
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
if ("Date" in df_filtered.columns) or date_col:
    try:
        date_col_use = "Date" if "Date" in df_filtered.columns else date_col
        df_filtered[date_col_use] = pd.to_datetime(df_filtered[date_col_use], errors="coerce")
        df_filtered = df_filtered.dropna(subset=[date_col_use])
        if len(df_filtered) > 0 and "Cout" in df_filtered.columns:
            df_filtered["Mois"] = df_filtered[date_col_use].dt.to_period("M").astype(str)
            df_mois = df_filtered.groupby("Mois")["Cout"].apply(lambda s: clean_numeric_series(s).sum(min_count=1)).reset_index()
            if not df_mois.empty:
                fig4 = px.line(df_mois, x="Mois", y="Cout", title="Coût total par mois (€)")
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Pas de données mensuelles de coût à afficher.")
        else:
            st.info("Données Date ou Cout insuffisantes pour l'évolution mensuelle.")
    except Exception:
        st.error("Erreur évolution mensuelle :")
        st.text(traceback.format_exc())
else:
    st.info("Colonne 'Date' absente : impossible de tracer l'évolution mensuelle.")

st.markdown("---")
st.markdown("**Conseils**")
st.markdown("- Activez le debug dans la sidebar pour voir les colonnes et aperçus si un graphique manque.")
st.markdown("- Si une colonne n'est pas détectée automatiquement (ex: Prix du KwH), vérifiez le nom exact dans le debug et adaptez vos données ou la logique de détection.")
st.markdown("- Pour le graphique 'Temps par type de borne', fournissez idéalement une colonne 'TYPE_BORNE' et 'TEMPS en min' ; sinon le fallback par station est affiché.")
