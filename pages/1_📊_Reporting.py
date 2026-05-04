import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import load_data

# --- MODE SOMBRE CUPRA ---
if "theme_cupra" not in st.session_state:
    st.session_state.theme_cupra = False

if st.session_state.theme_cupra:
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

# --- FILTRES EN CASCADE ---
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

df_filtered = df_temp.copy()
if lieu_filter != "Tous":
    df_filtered = df_filtered[df_filtered["LIEUX"] == lieu_filter]


st.divider()

# --- INDICATEURS CLÉS ---
st.subheader("📈 Indicateurs clés")

col1, col2, col3 = st.columns(3)

# Coût moyen le plus bas
cout_moyen = df_filtered.groupby("LIEUX")["Cout"].mean().sort_values()
if len(cout_moyen) > 0:
    col1.metric("Lieu le moins cher (moyenne)", cout_moyen.index[0], f"{cout_moyen.iloc[0]:.2f} €")

# Vitesse moyenne la plus élevée
if "Vitesse kw/min" in df_filtered.columns:
    vitesse_moyenne = df_filtered.groupby("LIEUX")["Vitesse kw/min"].mean().sort_values(ascending=False)
    if len(vitesse_moyenne) > 0:
        col2.metric("Lieu le plus rapide", vitesse_moyenne.index[0], f"{vitesse_moyenne.iloc[0]:.2f} kw/min")
else:
    col2.info("Colonne 'Vitesse kw/min' absente.")

# Nombre de sessions
col3.metric("Nombre de sessions", len(df_filtered))

st.divider()

# --- TOP 10 MOINS CHÈRES ---
st.subheader("💚 Top 10 des stations les moins chères (coût moyen)")

if len(cout_moyen) > 0:
    top10_low = cout_moyen.head(10).reset_index()
    fig_low = px.bar(
        top10_low, x="Cout", y="LIEUX", orientation="h",
        title="Top 10 des stations les moins chères (coût moyen)",
        labels={"Cout": "Coût moyen (€)", "LIEUX": "Station"}
    )
    st.plotly_chart(fig_low, use_container_width=True)

# --- TOP 10 PLUS CHÈRES ---
st.subheader("❤️ Top 10 des stations les plus chères (coût moyen)")

cout_moyen_high = df_filtered.groupby("LIEUX")["Cout"].mean().sort_values(ascending=False)
if len(cout_moyen_high) > 0:
    top10_high = cout_moyen_high.head(10).reset_index()
    fig_high = px.bar(
        top10_high, x="Cout", y="LIEUX", orientation="h",
        title="Top 10 des stations les plus chères (coût moyen)",
        labels={"Cout": "Coût moyen (€)", "LIEUX": "Station"}
    )
    st.plotly_chart(fig_high, use_container_width=True)

# --- TOP 10 PLUS RAPIDES ---
st.subheader("⚡ Top 10 des stations les plus rapides (vitesse moyenne)")

if "Vitesse kw/min" in df_filtered.columns:
    vitesse_moyenne_full = df_filtered.groupby("LIEUX")["Vitesse kw/min"].mean().sort_values(ascending=False)
    if len(vitesse_moyenne_full) > 0:
        top10_fast = vitesse_moyenne_full.head(10).reset_index()
        fig_fast = px.bar(
            top10_fast, x="Vitesse kw/min", y="LIEUX", orientation="h",
            title="Top 10 des stations les plus rapides (kw/min)",
            labels={"Vitesse kw/min": "Vitesse moyenne (kw/min)", "LIEUX": "Station"}
        )
        st.plotly_chart(fig_fast, use_container_width=True)

st.divider()

# --- DONUT : SESSIONS ---
st.subheader("🧁 Répartition du nombre de sessions par station")

sessions = df_filtered["LIEUX"].value_counts()
if len(sessions) > 0:
    fig_sessions = px.pie(
        names=sessions.index, values=sessions.values, hole=0.5,
        title="Répartition des sessions par station"
    )
    st.plotly_chart(fig_sessions, use_container_width=True)

# --- DONUT : COÛT PAR RÉGION ---
st.subheader("🧁 Répartition du coût total par région")

cout_region = df_filtered.groupby("REGION")["Cout"].sum()
if len(cout_region) > 0:
    fig_region = px.pie(
        names=cout_region.index, values=cout_region.values, hole=0.5,
        title="Répartition du coût total par région"
    )
    st.plotly_chart(fig_region, use_container_width=True)

# --- DONUT : TEMPS PAR TYPE DE BORNE ---
st.subheader("🧁 Répartition du temps passé par type de borne")

if "TYPE_BORNE" in df_filtered.columns and "TEMPS" in df_filtered.columns:
    temps_borne = df_filtered.groupby("TYPE_BORNE")["TEMPS"].sum()
    fig_temps = px.pie(
        names=temps_borne.index, values=temps_borne.values, hole=0.5,
        title="Répartition du temps passé par type de borne"
    )
    st.plotly_chart(fig_temps, use_container_width=True)

st.divider()

# --- RADAR CHART COMPARATIF ---
st.subheader("🛡️ Comparatif entre deux stations")

stations = df_filtered["LIEUX"].dropna().unique()
colA, colB = st.columns(2)
station_A = colA.selectbox("Station A", stations)
station_B = colB.selectbox("Station B", stations)

def stats_station(df, station):
    subset = df[df["LIEUX"] == station]
    return {
        "Coût moyen (€)": subset["Cout"].mean(),
        "Vitesse moyenne (kw/min)": subset["Vitesse kw/min"].mean() if "Vitesse kw/min" in df.columns else 0,
        "Sessions": len(subset),
        "Temps moyen (min)": subset["TEMPS"].mean() if "TEMPS" in df.columns else 0
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

