import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import load_data

# --- MODE SOMBRE CUPRA ---
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

df = load_data()

# --- FILTRES ---
st.subheader("🔍 Filtres")

regions = df["REGION"].dropna().unique()
region_filter = st.selectbox("Région", ["Toutes"] + list(regions))

df_temp = df.copy()
if region_filter != "Toutes":
    df_temp = df_temp[df_temp["REGION"] == region_filter]

lieux = df_temp["LIEUX"].dropna().unique()
lieu_filter = st.selectbox("Lieu", ["Tous"] + list(lieux))

df_filtered = df_temp.copy()
if lieu_filter != "Tous":
    df_filtered = df_filtered[df_filtered["LIEUX"] == lieu_filter]

st.divider()

# --- RÉSUMÉ GLOBAL ---
st.subheader("📌 Résumé global")

# 1) On calcule les valeurs AVANT d'appeler card()
cout_total = df_filtered["Cout"].sum()
prix_kwh_global = df_filtered["Prix du KwH"].mean()
vitesse_moyenne_global = df_filtered["Vitesse kw/min"].mean() if "Vitesse kw/min" in df_filtered.columns else None
temps_total = df_filtered["TEMPS en min"].sum() if "TEMPS en min" in df_filtered.columns else None

# 2) On définit la fonction card()
def card(label, value, accent=None):
    return f"""
    <div style='padding:14px; border-radius:10px; background-color:#1a1a1a; color:#e6e6e6;'>
        <div style='font-size:14px; opacity:0.8;'>{label}</div>
        <div style='font-size:22px; font-weight:600;'>{value}</div>
        {f"<div style='font-size:14px; color:#d47f2a;'>{accent}</div>" if accent else ""}
    </div>
    """

# 3) On affiche les cartes
colA, colB, colC, colD = st.columns(4)

colA.markdown(card("Coût total (€)", f"{cout_total:.2f}"), unsafe_allow_html=True)
colB.markdown(card("Prix moyen du kWh", f"{prix_kwh_global:.3f} €/kWh"), unsafe_allow_html=True)
colC.markdown(card("Vitesse moyenne", f"{vitesse_moyenne_global:.2f} kw/min" if vitesse_moyenne_global else "N/A"), unsafe_allow_html=True)
colD.markdown(card("Temps total", f"{temps_total:.1f} min" if temps_total else "N/A"), unsafe_allow_html=True)

st.divider()

# --- INDICATEURS CLÉS ---
st.subheader("📈 Indicateurs clés")

# 1) Calcul des valeurs AVANT l'affichage
prix_kwh_moyen_all = (
    df_filtered.groupby("LIEUX")["Prix du KwH"]
    .mean()
    .sort_values()
)

if "Vitesse kw/min" in df_filtered.columns:
    vitesse_moyenne_all = (
        df_filtered.groupby("LIEUX")["Vitesse kw/min"]
        .mean()
        .sort_values(ascending=False)
    )
else:
    vitesse_moyenne_all = None

nb_sessions = len(df_filtered)

# 2) Fonction carte HTML CUPRA
def card(label, value, accent=None):
    return f"""
    <div style='padding:14px; border-radius:10px; background-color:#1a1a1a; color:#e6e6e6;'>
        <div style='font-size:14px; opacity:0.8;'>{label}</div>
        <div style='font-size:20px; font-weight:600;'>{value}</div>
        {f"<div style='font-size:14px; color:#d47f2a;'>{accent}</div>" if accent else ""}
    </div>
    """

# 3) Affichage des cartes
col1, col2, col3 = st.columns(3)

# Station la moins chère
if len(prix_kwh_moyen_all) > 0:
    station_cheap = prix_kwh_moyen_all.index[0]
    prix_cheap = prix_kwh_moyen_all.iloc[0]
    col1.markdown(
        card("Station la moins chère", station_cheap, f"{prix_cheap:.3f} €/kWh"),
        unsafe_allow_html=True
    )
else:
    col1.markdown(card("Station la moins chère", "N/A"), unsafe_allow_html=True)

# Station la plus rapide
if vitesse_moyenne_all is not None and len(vitesse_moyenne_all) > 0:
    station_fast = vitesse_moyenne_all.index[0]
    vitesse_fast = vitesse_moyenne_all.iloc[0]
    col2.markdown(
        card("Station la plus rapide", station_fast, f"{vitesse_fast:.2f} kw/min"),
        unsafe_allow_html=True
    )
else:
    col2.markdown(card("Station la plus rapide", "N/A"), unsafe_allow_html=True)

# Nombre de sessions
col3.markdown(
    card("Nombre de sessions", f"{nb_sessions}"),
    unsafe_allow_html=True
)

st.divider()


# --- TOP 10 MOINS CHÈRES ---
st.subheader("💚 Top 10 des stations les moins chères (€/kWh)")

prix_kwh_moyen = (
    df_filtered.groupby("LIEUX")["Prix du KwH"]
    .mean()
    .sort_values()
    .head(10)
    .reset_index()
    .iloc[::-1]  # inversion pour afficher la moins chère en haut
)

fig_low = px.bar(
    prix_kwh_moyen,
    x="Prix du KwH",
    y="LIEUX",
    orientation="h",
    title="Top 10 des stations les moins chères (€/kWh)",
)

fig_low.update_traces(
    texttemplate='%{x:.3f}',
    textposition='outside'
)

st.plotly_chart(fig_low, use_container_width=True)

# --- TOP 10 PLUS CHÈRES ---
st.subheader("❤️ Top 10 des stations les plus chères (€/kWh)")

prix_kwh_moyen_high = (
    df_filtered.groupby("LIEUX")["Prix du KwH"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
    .iloc[::-1]
)

fig_high = px.bar(
    prix_kwh_moyen_high,
    x="Prix du KwH",
    y="LIEUX",
    orientation="h",
    title="Top 10 des stations les plus chères (€/kWh)",
)

fig_high.update_traces(
    texttemplate='%{x:.3f}',
    textposition='outside'
)

st.plotly_chart(fig_high, use_container_width=True)

st.divider()

# --- TOP 10 PLUS RAPIDES ---
st.subheader("⚡ Top 10 des stations les plus rapides (kw/min)")

if "Vitesse kw/min" in df_filtered.columns:
    vitesse_moyenne_full = (
        df_filtered.groupby("LIEUX")["Vitesse kw/min"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .iloc[::-1]
    )

    fig_fast = px.bar(
        vitesse_moyenne_full,
        x="Vitesse kw/min",
        y="LIEUX",
        orientation="h",
        title="Top 10 des stations les plus rapides (kw/min)",
    )

    fig_fast.update_traces(
        texttemplate='%{x:.2f}',
        textposition='outside'
    )

    st.plotly_chart(fig_fast, use_container_width=True)

st.divider()

# --- DONUT : SESSIONS ---
st.subheader("🧁 Répartition du nombre de sessions par station")

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

# --- DONUT : COÛT PAR RÉGION ---
st.subheader("🧁 Répartition du coût total par région")

cout_region = df_filtered.groupby("REGION")["Cout"].sum()
if len(cout_region) > 0:
    fig_region = px.pie(
        names=cout_region.index,
        values=cout_region.values,
        hole=0.5,
        title="Répartition du coût total par région"
    )
    fig_region.update_traces(textinfo='value')
    st.plotly_chart(fig_region, use_container_width=True)

# --- DONUT : TEMPS PAR TYPE DE BORNE ---
st.subheader("🧁 Répartition du temps passé par type de borne")

if "TYPE_BORNE" in df_filtered.columns and "TEMPS en min" in df_filtered.columns:
    temps_borne = df_filtered.groupby("TYPE_BORNE")["TEMPS en min"].sum()
    fig_temps = px.pie(
        names=temps_borne.index,
        values=temps_borne.values,
        hole=0.5,
        title="Répartition du temps passé par type de borne"
    )
    fig_temps.update_traces(textinfo='label+value')
    st.plotly_chart(fig_temps, use_container_width=True)

st.divider()

# --- RADAR CHART ---
st.subheader("🛡️ Comparatif entre deux stations")

stations = df_filtered["LIEUX"].dropna().unique()
colA, colB = st.columns(2)
station_A = colA.selectbox("Station A", stations)
station_B = colB.selectbox("Station B", stations)

def stats_station(df, station):
    subset = df[df["LIEUX"] == station]
    return {
        "Prix moyen du kWh": subset["Prix du KwH"].mean(),
        "Vitesse moyenne (kw/min)": subset["Vitesse kw/min"].mean() if "Vitesse kw/min" in df.columns else 0,
        "Sessions": len(subset),
        "Temps moyen (min)": subset["TEMPS en min"].mean() if "TEMPS en min" in df.columns else 0
    }

stats_A = stats_station(df_filtered, station_A)
stats_B = stats_station(df_filtered, station_B)

categories = list(stats_A.keys())

fig_radar = go.Figure()

fig_radar.add_trace(go.Scatterpolar(
    r=list(stats_A.values()), theta=categories, fill='toself', name=station_A
))
fig_radar.add_trace(go.Scatterpolar(
    r=list(stats_B.values()), theta=categories, fill='toself', name=station_B
))

fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True)),
    title="Comparatif des performances entre deux stations"
)

st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# --- ÉVOLUTION MENSUELLE ---
st.subheader("📅 Évolution mensuelle du coût")

df_filtered["Date"] = pd.to_datetime(df_filtered["Date"], errors="coerce")
df_filtered = df_filtered.dropna(subset=["Date"])

if len(df_filtered) > 0:
    df_filtered["Mois"] = df_filtered["Date"].dt.to_period("M").astype(str)
    df_mois = df_filtered.groupby("Mois")["Cout"].sum().reset_index()

    fig4 = px.line(
        df_mois, x="Mois", y="Cout",
        title="Coût total par mois (€)"
    )
    st.plotly_chart(fig4, use_container_width=True)
